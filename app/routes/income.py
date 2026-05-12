from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Income
from datetime import datetime

bp = Blueprint('income', __name__, url_prefix='/income')

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    source = request.args.get('source', '').strip()
    
    # Build query
    query = Income.query.filter_by(user_id=current_user.id)
    
    # Search by description
    if search_query:
        query = query.filter(Income.description.ilike(f'%{search_query}%'))
    
    # Filter by date range
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Income.date >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Income.date <= end)
        except ValueError:
            pass
    
    # Filter by source
    if source:
        query = query.filter(Income.source.ilike(f'%{source}%'))
    
    # Order and paginate
    incomes = query.order_by(Income.date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get unique sources for filter
    sources = db.session.query(Income.source).filter_by(user_id=current_user.id)\
        .distinct().all()
    unique_sources = [s[0] for s in sources if s[0]]
    
    return render_template('income/index.html', 
                         incomes=incomes,
                         search_query=search_query,
                         start_date=start_date,
                         end_date=end_date,
                         selected_source=source,
                         sources=unique_sources)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        amount = request.form.get('amount')
        description = request.form.get('description')
        date = request.form.get('date')
        source = request.form.get('source', '').strip()
        
        try:
            income = Income(
                amount=float(amount),
                description=description,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                source=source if source else None,
                user_id=current_user.id
            )
            db.session.add(income)
            db.session.commit()
            flash('Income added successfully', 'success')
            return redirect(url_for('income.index'))
        except Exception as e:
            flash(f'Error adding income: {str(e)}', 'error')
    
    return render_template('income/add.html')

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    income = Income.query.get_or_404(id)
    
    if income.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('income.index'))
    
    if request.method == 'POST':
        income.amount = float(request.form.get('amount'))
        income.description = request.form.get('description')
        income.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        income.source = request.form.get('source', '').strip() or None
        
        db.session.commit()
        flash('Income updated successfully', 'success')
        return redirect(url_for('income.index'))
    
    return render_template('income/edit.html', income=income)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    income = Income.query.get_or_404(id)
    
    if income.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('income.index'))
    
    db.session.delete(income)
    db.session.commit()
    flash('Income deleted successfully', 'success')
    return redirect(url_for('income.index'))

@bp.route('/api/total')
@login_required
def api_total():
    """Get total income for a date range"""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    query = db.session.query(db.func.sum(Income.amount)).filter_by(user_id=current_user.id)
    
    if start_date:
        query = query.filter(Income.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Income.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    total = query.scalar() or 0
    return jsonify({'total': float(total)})

