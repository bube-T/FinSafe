from flask import Blueprint, render_template, jsonify, request, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Income, Budget, Category
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from collections import defaultdict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    today = datetime.now()
    return render_template('reports/index.html', 
                         current_month=today.month,
                         current_year=today.year)

@bp.route('/monthly')
@login_required
def monthly():
    """Generate monthly spending report"""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    today = datetime.now()
    if not month:
        month = today.month
    if not year:
        year = today.year
    
    start_date = datetime(year, month, 1).date()
    # Get last day of month
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get all expenses for the month
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).order_by(Expense.date.desc()).all()
    
    # Calculate totals
    total_spending = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).scalar() or 0
    
    # Group by category
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    
    for expense in expenses:
        category_name = expense.category.name if expense.category else 'Uncategorized'
        category_totals[category_name] += float(expense.amount)
        category_counts[category_name] += 1
    
    # Get budgets for the month
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        period='monthly',
        month=month,
        year=year
    ).all()
    
    budget_data = [b.to_dict() for b in budgets]
    
    # Calculate average daily spending
    days_in_month = (end_date - start_date).days + 1
    avg_daily = float(total_spending) / days_in_month if days_in_month > 0 else 0
    
    return render_template('reports/monthly.html',
                         expenses=expenses,
                         total_spending=float(total_spending),
                         category_totals=dict(category_totals),
                         category_counts=dict(category_counts),
                         budgets=budget_data,
                         month=month,
                         year=year,
                         month_name=datetime(year, month, 1).strftime('%B'),
                         avg_daily=round(avg_daily, 2),
                         days_in_month=days_in_month)

@bp.route('/yearly')
@login_required
def yearly():
    """Generate yearly spending report"""
    year = request.args.get('year', type=int)
    
    if not year:
        year = datetime.now().year
    
    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()
    
    # Get all expenses for the year
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).order_by(Expense.date.desc()).all()
    
    # Calculate totals
    total_spending = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).scalar() or 0
    
    # Group by month
    monthly_totals = defaultdict(float)
    monthly_counts = defaultdict(int)
    
    for expense in expenses:
        month_key = expense.date.strftime('%B')
        monthly_totals[month_key] += float(expense.amount)
        monthly_counts[month_key] += 1
    
    # Group by category
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    
    for expense in expenses:
        category_name = expense.category.name if expense.category else 'Uncategorized'
        category_totals[category_name] += float(expense.amount)
        category_counts[category_name] += 1
    
    # Calculate average monthly spending
    avg_monthly = float(total_spending) / 12 if total_spending > 0 else 0
    
    # Get monthly breakdown for chart
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data = {month: monthly_totals.get(month, 0) for month in month_order}
    
    return render_template('reports/yearly.html',
                         expenses=expenses,
                         total_spending=float(total_spending),
                         monthly_totals=monthly_data,
                         monthly_counts=dict(monthly_counts),
                         category_totals=dict(category_totals),
                         category_counts=dict(category_counts),
                         year=year,
                         avg_monthly=round(avg_monthly, 2))

