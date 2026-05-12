from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category
from datetime import datetime, timedelta

bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    category_id = request.args.get('category', type=int)
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    
    # Build query
    query = Expense.query.filter_by(user_id=current_user.id)
    
    # Search by description
    if search_query:
        query = query.filter(Expense.description.ilike(f'%{search_query}%'))
    
    # Filter by category
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    
    # Filter by date range
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= end)
        except ValueError:
            pass
    
    # Filter by amount range
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)
    
    # Order and paginate
    expenses = query.order_by(Expense.date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get categories for filter dropdown
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    return render_template('expenses/index.html', 
                         expenses=expenses, 
                         categories=categories,
                         search_query=search_query,
                         selected_category=category_id,
                         start_date=start_date,
                         end_date=end_date,
                         min_amount=min_amount,
                         max_amount=max_amount)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        amount = request.form.get('amount')
        description = request.form.get('description')
        date = request.form.get('date')
        category_id = request.form.get('category_id') or None
        
        try:
            expense = Expense(
                amount=float(amount),
                description=description,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                user_id=current_user.id,
                category_id=int(category_id) if category_id else None
            )
            db.session.add(expense)
            db.session.commit()
            flash('Expense added successfully', 'success')
            return redirect(url_for('expenses.index'))
        except Exception as e:
            flash(f'Error adding expense: {str(e)}', 'error')
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('expenses/add.html', categories=categories)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense = Expense.query.get_or_404(id)
    
    if expense.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('expenses.index'))
    
    if request.method == 'POST':
        expense.amount = float(request.form.get('amount'))
        expense.description = request.form.get('description')
        expense.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        category_id = request.form.get('category_id') or None
        expense.category_id = int(category_id) if category_id else None
        
        db.session.commit()
        flash('Expense updated successfully', 'success')
        return redirect(url_for('expenses.index'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('expenses/edit.html', expense=expense, categories=categories)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    expense = Expense.query.get_or_404(id)
    
    if expense.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('expenses.index'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully', 'success')
    return redirect(url_for('expenses.index'))

@bp.route('/api/recent')
@login_required
def api_recent():
    limit = request.args.get('limit', 10, type=int)
    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc())\
        .limit(limit)\
        .all()
    
    return jsonify([expense.to_dict() for expense in expenses])

@bp.route('/api/by-date-range')
@login_required
def api_by_date_range():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if start_date:
        query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    expenses = query.order_by(Expense.date.desc()).all()
    return jsonify([expense.to_dict() for expense in expenses])

