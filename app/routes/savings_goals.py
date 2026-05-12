from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import SavingsGoal
from datetime import datetime

bp = Blueprint('savings_goals', __name__, url_prefix='/savings-goals')

@bp.route('/')
@login_required
def index():
    goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.created_at.desc()).all()
    goals_data = [goal.to_dict() for goal in goals]
    return render_template('savings_goals/index.html', goals=goals_data)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        target_amount = request.form.get('target_amount')
        current_amount = request.form.get('current_amount', 0)
        target_date = request.form.get('target_date') or None
        
        try:
            goal = SavingsGoal(
                name=name,
                target_amount=float(target_amount),
                current_amount=float(current_amount),
                target_date=datetime.strptime(target_date, '%Y-%m-%d').date() if target_date else None,
                user_id=current_user.id
            )
            db.session.add(goal)
            db.session.commit()
            flash('Savings goal created successfully', 'success')
            return redirect(url_for('savings_goals.index'))
        except Exception as e:
            flash(f'Error creating savings goal: {str(e)}', 'error')
    
    return render_template('savings_goals/add.html')

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    goal = SavingsGoal.query.get_or_404(id)
    
    if goal.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('savings_goals.index'))
    
    if request.method == 'POST':
        goal.name = request.form.get('name')
        goal.target_amount = float(request.form.get('target_amount'))
        goal.current_amount = float(request.form.get('current_amount', 0))
        target_date = request.form.get('target_date') or None
        goal.target_date = datetime.strptime(target_date, '%Y-%m-%d').date() if target_date else None
        
        db.session.commit()
        flash('Savings goal updated successfully', 'success')
        return redirect(url_for('savings_goals.index'))
    
    return render_template('savings_goals/edit.html', goal=goal)

@bp.route('/update-progress/<int:id>', methods=['POST'])
@login_required
def update_progress(id):
    """Update the current amount for a savings goal"""
    goal = SavingsGoal.query.get_or_404(id)
    
    if goal.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        new_amount = float(request.json.get('current_amount', 0))
        goal.current_amount = new_amount
        db.session.commit()
        return jsonify(goal.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    goal = SavingsGoal.query.get_or_404(id)
    
    if goal.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('savings_goals.index'))
    
    db.session.delete(goal)
    db.session.commit()
    flash('Savings goal deleted successfully', 'success')
    return redirect(url_for('savings_goals.index'))

