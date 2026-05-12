from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Budget, Category
from datetime import datetime

bp = Blueprint('budgets', __name__, url_prefix='/budgets')

@bp.route('/')
@login_required
def index():
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    budget_data = [budget.to_dict() for budget in budgets]
    return render_template('budgets/index.html', budgets=budget_data)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        amount = request.form.get('amount')
        period = request.form.get('period')
        alert_threshold = request.form.get('alert_threshold', 80)
        category_id = request.form.get('category_id') or None
        
        try:
            today = datetime.now()
            budget = Budget(
                amount=float(amount),
                period=period,
                alert_threshold=float(alert_threshold),
                user_id=current_user.id,
                category_id=int(category_id) if category_id else None,
                month=today.month if period == 'monthly' else None,
                year=today.year if period == 'monthly' else None
            )
            db.session.add(budget)
            db.session.commit()
            flash('Budget created successfully', 'success')
            return redirect(url_for('budgets.index'))
        except Exception as e:
            flash(f'Error creating budget: {str(e)}', 'error')
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets/add.html', categories=categories)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    budget = Budget.query.get_or_404(id)
    
    if budget.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('budgets.index'))
    
    if request.method == 'POST':
        budget.amount = float(request.form.get('amount'))
        budget.period = request.form.get('period')
        budget.alert_threshold = float(request.form.get('alert_threshold', 80))
        category_id = request.form.get('category_id') or None
        budget.category_id = int(category_id) if category_id else None
        
        db.session.commit()
        flash('Budget updated successfully', 'success')
        return redirect(url_for('budgets.index'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets/edit.html', budget=budget, categories=categories)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    budget = Budget.query.get_or_404(id)
    
    if budget.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('budgets.index'))
    
    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully', 'success')
    return redirect(url_for('budgets.index'))

@bp.route('/api/list')
@login_required
def api_list():
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return jsonify([budget.to_dict() for budget in budgets])

