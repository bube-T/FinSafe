import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app import db, mail
from app.models import Budget, User
from flask_mail import Message
from datetime import datetime


class _CircuitBreaker:
    """
    Simple circuit breaker for the SMTP email dependency.
    States: CLOSED (normal) → OPEN (failing, fast-fail) → HALF_OPEN (probe).
    Prevents a slow/down mail server from blocking the scheduler thread for
    every user's budget check.
    """
    FAILURE_THRESHOLD = 3    # consecutive failures before opening
    RESET_TIMEOUT     = 300  # seconds to wait before probing again

    def __init__(self):
        self._failures    = 0
        self._state       = 'CLOSED'
        self._last_fail   = 0.0

    def call(self, func, *args, **kwargs):
        if self._state == 'OPEN':
            if time.time() - self._last_fail >= self.RESET_TIMEOUT:
                self._state = 'HALF_OPEN'
                print('Email circuit: HALF_OPEN — probing')
            else:
                raise RuntimeError('Email circuit OPEN — skipping send')

        try:
            result = func(*args, **kwargs)
            if self._state == 'HALF_OPEN':
                self._state    = 'CLOSED'
                self._failures = 0
                print('Email circuit: CLOSED — recovered')
            return result
        except Exception as exc:
            self._failures  += 1
            self._last_fail  = time.time()
            if self._failures >= self.FAILURE_THRESHOLD:
                if self._state != 'OPEN':
                    print(f'Email circuit: OPEN after {self._failures} failures')
                self._state = 'OPEN'
            raise exc


_email_breaker = _CircuitBreaker()


def send_budget_alert_email(user, budget, percentage):
    """Send email alert with circuit-breaker protection around mail.send()."""
    try:
        category_name = budget.category.name if budget.category else 'All Categories'
        spending      = budget.get_current_spending()

        if percentage >= 100:
            subject = f'FinSafe Budget Alert: {category_name} EXCEEDED'
            body = (
                f'Your budget for {category_name} has been EXCEEDED!\n\n'
                f'Budget:   £{float(budget.amount):.2f}\n'
                f'Spent:    £{spending:.2f} ({percentage:.1f}%)\n'
                f'Period:   {budget.period.title()}\n\n'
                'Visit FinSafe to review your budgets.'
            )
        else:
            subject = f'FinSafe Budget Alert: {category_name} at {percentage:.1f}%'
            body = (
                f'Your {category_name} budget is approaching its limit.\n\n'
                f'Budget:    £{float(budget.amount):.2f}\n'
                f'Spent:     £{spending:.2f} ({percentage:.1f}%)\n'
                f'Remaining: £{float(budget.amount) - spending:.2f}\n'
                f'Period:    {budget.period.title()}\n\n'
                'Visit FinSafe to manage your budgets.'
            )

        msg = Message(subject=subject, recipients=[user.email], body=body)
        _email_breaker.call(mail.send, msg)
        return True

    except RuntimeError:
        # Circuit is OPEN — log and skip silently
        print(f'Email skipped (circuit open) for user {user.id}')
        return False
    except Exception as exc:
        print(f'Email error for user {user.id}: {exc}')
        return False


def check_budget_alerts(app):
    """Check all budgets and send alerts when threshold is reached."""
    with app.app_context():
        budgets     = Budget.query.all()
        alerts_sent = []

        for budget in budgets:
            percentage = budget.get_percentage_used()
            if percentage >= float(budget.alert_threshold):
                user = User.query.get(budget.user_id)
                if user and user.email:
                    sent = send_budget_alert_email(user, budget, percentage)
                    alerts_sent.append({
                        'user_id':    budget.user_id,
                        'budget_id':  budget.id,
                        'category':   budget.category.name if budget.category else 'All Categories',
                        'percentage': percentage,
                        'email_sent': sent,
                    })
                    print(
                        f'ALERT: user {budget.user_id} — '
                        f'{alerts_sent[-1]["category"]} at {percentage:.1f}% '
                        f'(email: {sent})'
                    )

        return alerts_sent


def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: check_budget_alerts(app),
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_budget_check',
        name='Daily Budget Alert Check',
        replace_existing=True,
    )
    scheduler.start()
    print('Scheduler started — budget alerts checked daily at 09:00')
    return scheduler
