from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app import db, mail
from app.models import Budget, User
from flask_mail import Message
from datetime import datetime

def send_budget_alert_email(user, budget, percentage):
    """Send email alert for budget threshold"""
    try:
        category_name = budget.category.name if budget.category else 'All Categories'
        spending = budget.get_current_spending()
        
        subject = f"FinSafe Budget Alert: {category_name} at {percentage:.1f}%"
        
        if percentage >= 100:
            alert_level = "EXCEEDED"
            message_body = f"""
Your budget for {category_name} has been EXCEEDED!

Budget Details:
- Category: {category_name}
- Budget Amount: £{budget.amount:.2f}
- Current Spending: £{spending:.2f}
- Percentage Used: {percentage:.1f}%
- Period: {budget.period.title()}

Please review your spending and adjust your budget if needed.

Visit FinSafe to manage your budgets: http://localhost:5000/budgets
"""
        else:
            alert_level = "WARNING"
            message_body = f"""
Your budget for {category_name} is approaching its limit!

Budget Details:
- Category: {category_name}
- Budget Amount: £{budget.amount:.2f}
- Current Spending: £{spending:.2f}
- Remaining: £{budget.amount - spending:.2f}
- Percentage Used: {percentage:.1f}%
- Period: {budget.period.title()}

You're at {percentage:.1f}% of your budget. Consider monitoring your spending.

Visit FinSafe to manage your budgets: http://localhost:5000/budgets
"""
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=message_body
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email alert: {str(e)}")
        return False

def check_budget_alerts(app):
    """Check all budgets and send alerts if threshold is reached"""
    with app.app_context():
        budgets = Budget.query.all()
        alerts_sent = []
        
        for budget in budgets:
            percentage = budget.get_percentage_used()
            
            # Check if threshold is reached (80% or 100%)
            if percentage >= budget.alert_threshold:
                user = User.query.get(budget.user_id)
                if user and user.email:
                    # Send email alert
                    email_sent = send_budget_alert_email(user, budget, percentage)
                    
                    alert_info = {
                        'user_id': budget.user_id,
                        'budget_id': budget.id,
                        'category': budget.category.name if budget.category else 'All Categories',
                        'percentage': percentage,
                        'spending': budget.get_current_spending(),
                        'limit': float(budget.amount),
                        'period': budget.period,
                        'email_sent': email_sent
                    }
                    alerts_sent.append(alert_info)
                    
                    # Log alert
                    print(f"ALERT: User {budget.user_id} ({user.email}) - Budget for '{alert_info['category']}' "
                          f"is at {percentage:.1f}% (Email sent: {email_sent})")
        
        return alerts_sent

def init_scheduler(app):
    """Initialize the scheduler for budget alerts"""
    scheduler = BackgroundScheduler()
    
    # Check budgets daily at 9 AM
    scheduler.add_job(
        func=lambda: check_budget_alerts(app),
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_budget_check',
        name='Daily Budget Alert Check',
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started - Budget alerts will be checked daily at 9 AM")
    
    return scheduler

