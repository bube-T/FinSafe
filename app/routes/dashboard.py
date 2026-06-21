from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Income, Budget, Category, SavingsGoal
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from collections import defaultdict

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def root():
    """Root route - redirect to dashboard or login"""
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
    """CV-spec endpoint: total income, total expenses, and spending by category for the current month"""
    today = datetime.now()
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
        'total_income': round(float(total_income), 2),
        'total_expenses': round(float(total_expenses), 2),
        'by_category': dict(by_category)
    })

@bp.route('/api/spending-trends')
@login_required
def api_spending_trends():
    """Get spending trends for the last 6 months"""
    six_months_ago = datetime.now() - timedelta(days=180)
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= six_months_ago.date()
    ).all()
    
    # Group by month
    monthly_spending = defaultdict(float)
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        monthly_spending[month_key] += float(expense.amount)
    
    # Sort by month
    sorted_months = sorted(monthly_spending.keys())
    
    return jsonify({
        'labels': sorted_months,
        'data': [monthly_spending[month] for month in sorted_months]
    })

@bp.route('/api/category-breakdown')
@login_required
def api_category_breakdown():
    """Get spending breakdown by category for current month"""
    today = datetime.now()
    start_of_month = today.replace(day=1).date()
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_of_month
    ).all()
    
    category_spending = defaultdict(float)
    uncategorized = 0.0
    
    for expense in expenses:
        if expense.category:
            category_spending[expense.category.name] += float(expense.amount)
        else:
            uncategorized += float(expense.amount)
    
    if uncategorized > 0:
        category_spending['Uncategorized'] = uncategorized
    
    return jsonify({
        'labels': list(category_spending.keys()),
        'data': list(category_spending.values())
    })

@bp.route('/api/monthly-summary')
@login_required
def api_monthly_summary():
    """Get summary for current month"""
    today = datetime.now()
    start_of_month = today.replace(day=1).date()
    
    total_spending = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_of_month
    ).scalar() or 0
    
    total_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == current_user.id,
        Income.date >= start_of_month
    ).scalar() or 0
    
    net_cash_flow = float(total_income) - float(total_spending)
    
    expense_count = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_of_month
    ).count()
    
    # Get average daily spending
    days_in_month = today.day
    avg_daily = float(total_spending) / days_in_month if days_in_month > 0 else 0
    
    # Get budget status
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    budget_alerts = [b.to_dict() for b in budgets if b.is_alert_threshold_reached()]
    
    # Get spending vs budget by category for current month
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_budgets = []
    
    for category in categories:
        # Get budget for this category (monthly)
        budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category.id,
            period='monthly'
        ).first()
        
        if budget:
            # Calculate spending for this category this month
            category_spending = db.session.query(func.sum(Expense.amount)).filter(
                Expense.user_id == current_user.id,
                Expense.category_id == category.id,
                Expense.date >= start_of_month
            ).scalar() or 0
            
            category_budgets.append({
                'category_name': category.name,
                'category_color': category.color,
                'budget_amount': float(budget.amount),
                'spending': float(category_spending),
                'remaining': float(budget.amount) - float(category_spending),
                'percentage': (float(category_spending) / float(budget.amount) * 100) if budget.amount > 0 else 0
            })
    
    return jsonify({
        'total_spending': float(total_spending),
        'total_income': float(total_income),
        'net_cash_flow': round(net_cash_flow, 2),
        'expense_count': expense_count,
        'avg_daily': round(avg_daily, 2),
        'budget_alerts': budget_alerts,
        'category_budgets': category_budgets
    })

@bp.route('/api/recent-expenses')
@login_required
def api_recent_expenses():
    """Get recent expenses for dashboard"""
    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc())\
        .limit(10)\
        .all()
    
    return jsonify([expense.to_dict() for expense in expenses])

@bp.route('/api/net-worth')
@login_required
def api_net_worth():
    """Calculate net worth (total income - total expenses + savings goals)"""
    # Total income (all time)
    total_income = db.session.query(func.sum(Income.amount)).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    
    # Total expenses (all time)
    total_expenses = db.session.query(func.sum(Expense.amount)).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    
    # Total savings from goals
    total_savings = db.session.query(func.sum(SavingsGoal.current_amount)).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    
    # Net worth = Income - Expenses + Savings
    net_worth = float(total_income) - float(total_expenses) + float(total_savings)
    
    return jsonify({
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'total_savings': float(total_savings),
        'net_worth': round(net_worth, 2)
    })

@bp.route('/api/notifications')
@login_required
def api_notifications():
    """Return active budget alerts and completed savings goals as notifications."""
    notifications = []

    for b in Budget.query.filter_by(user_id=current_user.id).all():
        pct = b.get_percentage_used()
        if pct >= float(b.alert_threshold):
            label = b.category.name if b.category else 'Overall'
            over  = pct >= 100
            notifications.append({
                'type':     'budget_alert',
                'icon':     'warning' if not over else 'error',
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

    return jsonify({'count': len(notifications), 'notifications': notifications})

@bp.route('/api/savings-goals-summary')
@login_required
def api_savings_goals_summary():
    """Get summary of savings goals"""
    goals = SavingsGoal.query.filter_by(user_id=current_user.id).all()
    
    total_target = sum(float(g.target_amount) for g in goals)
    total_current = sum(float(g.current_amount) for g in goals)
    completed_count = sum(1 for g in goals if g.is_completed())
    
    return jsonify({
        'total_goals': len(goals),
        'completed_goals': completed_count,
        'total_target': round(total_target, 2),
        'total_current': round(total_current, 2),
        'total_progress': round((total_current / total_target * 100) if total_target > 0 else 0, 2),
        'goals': [g.to_dict() for g in goals]
    })

