from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db, cache
from app.models import Expense, Income, Budget, Category, SavingsGoal
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from collections import defaultdict
import os

bp = Blueprint('dashboard', __name__)


def _ck(suffix):
    """Build a per-user cache key."""
    return f'u{current_user.id}_{suffix}'


@bp.route('/api/health')
def health():
    db_url  = os.getenv('DATABASE_URL', 'not set')
    db_type = ('postgresql' if 'postgresql' in db_url or 'postgres' in db_url
               else 'sqlite' if 'sqlite' in db_url else 'unknown')
    try:
        from app.models import User
        user_count = User.query.count()
        db_ok = True
    except Exception:
        user_count = None
        db_ok = False
    return jsonify({
        'db_type': db_type,
        'db_connected': db_ok,
        'user_count': user_count,
        'DATABASE_URL_set': db_url != 'not set',
    })


@bp.route('/')
def root():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@bp.route('/dashboard')
@login_required
def index():
    return render_template('dashboard/index.html')


@bp.route('/api/summary')
@login_required
def api_summary():
    today          = datetime.now()
    start_of_month = today.replace(day=1).date()

    total_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == current_user.id,
        Income.date >= start_of_month
    ).scalar() or 0

    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_of_month
    ).scalar() or 0

    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_of_month
    ).all()

    by_category = defaultdict(float)
    for expense in expenses:
        label = expense.category.name if expense.category else 'Uncategorized'
        by_category[label] += float(expense.amount)

    return jsonify({
        'total_income':   round(float(total_income), 2),
        'total_expenses': round(float(total_expenses), 2),
        'by_category':    dict(by_category),
    })


@bp.route('/api/spending-trends')
@login_required
def api_spending_trends():
    key    = _ck('spending_trends')
    cached = cache.get(key)
    if cached is not None:
        return jsonify(cached)

    six_months_ago   = datetime.now() - timedelta(days=180)
    expenses         = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date    >= six_months_ago.date()
    ).all()

    monthly_spending = defaultdict(float)
    for expense in expenses:
        monthly_spending[expense.date.strftime('%Y-%m')] += float(expense.amount)

    sorted_months = sorted(monthly_spending)
    result = {
        'labels': sorted_months,
        'data':   [monthly_spending[m] for m in sorted_months],
    }
    cache.set(key, result, timeout=300)   # 5-minute TTL — changes slowly
    return jsonify(result)


@bp.route('/api/category-breakdown')
@login_required
def api_category_breakdown():
    key    = _ck('category_breakdown')
    cached = cache.get(key)
    if cached is not None:
        return jsonify(cached)

    today          = datetime.now()
    start_of_month = today.replace(day=1).date()
    expenses       = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date    >= start_of_month
    ).all()

    category_spending = defaultdict(float)
    uncategorized     = 0.0
    for expense in expenses:
        if expense.category:
            category_spending[expense.category.name] += float(expense.amount)
        else:
            uncategorized += float(expense.amount)
    if uncategorized:
        category_spending['Uncategorized'] = uncategorized

    result = {
        'labels': list(category_spending.keys()),
        'data':   list(category_spending.values()),
    }
    cache.set(key, result, timeout=120)
    return jsonify(result)


@bp.route('/api/monthly-summary')
@login_required
def api_monthly_summary():
    key    = _ck('monthly_summary')
    cached = cache.get(key)
    if cached is not None:
        return jsonify(cached)

    today          = datetime.now()
    start_of_month = today.replace(day=1).date()

    total_spending = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date    >= start_of_month
    ).scalar() or 0

    total_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == current_user.id,
        Income.date    >= start_of_month
    ).scalar() or 0

    expense_count = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date    >= start_of_month
    ).count()

    days_in_month = today.day
    avg_daily     = float(total_spending) / days_in_month if days_in_month else 0

    budgets       = Budget.query.filter_by(user_id=current_user.id).all()
    budget_alerts = [b.to_dict() for b in budgets if b.is_alert_threshold_reached()]

    categories      = Category.query.filter_by(user_id=current_user.id).all()
    category_budgets = []
    for category in categories:
        budget = Budget.query.filter_by(
            user_id=current_user.id, category_id=category.id, period='monthly'
        ).first()
        if budget:
            cat_spending = db.session.query(func.sum(Expense.amount)).filter(
                Expense.user_id     == current_user.id,
                Expense.category_id == category.id,
                Expense.date        >= start_of_month,
            ).scalar() or 0
            category_budgets.append({
                'category_name':  category.name,
                'category_color': category.color,
                'budget_amount':  float(budget.amount),
                'spending':       float(cat_spending),
                'remaining':      float(budget.amount) - float(cat_spending),
                'percentage':     (float(cat_spending) / float(budget.amount) * 100) if budget.amount else 0,
            })

    result = {
        'total_spending':   float(total_spending),
        'total_income':     float(total_income),
        'net_cash_flow':    round(float(total_income) - float(total_spending), 2),
        'expense_count':    expense_count,
        'avg_daily':        round(avg_daily, 2),
        'budget_alerts':    budget_alerts,
        'category_budgets': category_budgets,
    }
    cache.set(key, result, timeout=120)
    return jsonify(result)


@bp.route('/api/recent-expenses')
@login_required
def api_recent_expenses():
    key    = _ck('recent_expenses')
    cached = cache.get(key)
    if cached is not None:
        return jsonify(cached)

    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc()).limit(10).all()
    result   = [e.to_dict() for e in expenses]
    cache.set(key, result, timeout=60)
    return jsonify(result)


@bp.route('/api/net-worth')
@login_required
def api_net_worth():
    key    = _ck('net_worth')
    cached = cache.get(key)
    if cached is not None:
        return jsonify(cached)

    total_income   = db.session.query(func.sum(Income.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_savings  = db.session.query(func.sum(SavingsGoal.current_amount)).filter_by(user_id=current_user.id).scalar() or 0

    result = {
        'total_income':   float(total_income),
        'total_expenses': float(total_expenses),
        'total_savings':  float(total_savings),
        'net_worth':      round(float(total_income) - float(total_expenses) + float(total_savings), 2),
    }
    cache.set(key, result, timeout=120)
    return jsonify(result)


@bp.route('/api/notifications')
@login_required
def api_notifications():
    key    = _ck('notifications')
    cached = cache.get(key)
    if cached is not None:
        return jsonify(cached)

    notifications = []
    for b in Budget.query.filter_by(user_id=current_user.id).all():
        pct  = b.get_percentage_used()
        over = pct >= 100
        if pct >= float(b.alert_threshold):
            label = b.category.name if b.category else 'Overall'
            notifications.append({
                'type':     'budget_alert',
                'icon':     'error' if over else 'warning',
                'title':    f'{"Over" if over else "Approaching"} budget: {label}',
                'message':  f'{pct:.0f}% used — £{b.get_current_spending():.2f} of £{float(b.amount):.2f}',
                'severity': 'error' if over else 'warning',
            })
    for g in SavingsGoal.query.filter_by(user_id=current_user.id).all():
        if g.is_completed():
            notifications.append({
                'type':     'goal_complete',
                'icon':     'check_circle',
                'title':    f'Goal reached: {g.name}',
                'message':  f'You hit your £{float(g.target_amount):.0f} target!',
                'severity': 'success',
            })

    result = {'count': len(notifications), 'notifications': notifications}
    cache.set(key, result, timeout=60)
    return jsonify(result)


@bp.route('/api/savings-goals-summary')
@login_required
def api_savings_goals_summary():
    key    = _ck('savings_goals_summary')
    cached = cache.get(key)
    if cached is not None:
        return jsonify(cached)

    goals         = SavingsGoal.query.filter_by(user_id=current_user.id).all()
    total_target  = sum(float(g.target_amount)  for g in goals)
    total_current = sum(float(g.current_amount) for g in goals)

    result = {
        'total_goals':    len(goals),
        'completed_goals': sum(1 for g in goals if g.is_completed()),
        'total_target':   round(total_target, 2),
        'total_current':  round(total_current, 2),
        'total_progress': round((total_current / total_target * 100) if total_target else 0, 2),
        'goals':          [g.to_dict() for g in goals],
    }
    cache.set(key, result, timeout=120)
    return jsonify(result)
