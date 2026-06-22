from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category
from app.utils import clear_dashboard_cache
from datetime import datetime

bp = Blueprint('expenses', __name__, url_prefix='/expenses')


def _is_fetch(req):
    """True when the request came from a fetch() call, not a full form submit."""
    return (req.is_json
            or req.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or 'application/json' in req.headers.get('Accept', ''))


@bp.route('/')
@login_required
def index():
    page          = request.args.get('page', 1, type=int)
    search_query  = request.args.get('search', '').strip()
    category_id   = request.args.get('category', type=int)
    start_date    = request.args.get('start_date', '').strip()
    end_date      = request.args.get('end_date', '').strip()
    min_amount    = request.args.get('min_amount', type=float)
    max_amount    = request.args.get('max_amount', type=float)

    query = Expense.query.filter_by(user_id=current_user.id)
    if search_query:
        query = query.filter(Expense.description.ilike(f'%{search_query}%'))
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if start_date:
        try:
            query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        except ValueError:
            pass
    if end_date:
        try:
            query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        except ValueError:
            pass
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)

    expenses   = query.order_by(Expense.date.desc()).paginate(page=page, per_page=20, error_out=False)
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
        try:
            expense = Expense(
                amount=float(request.form.get('amount')),
                description=request.form.get('description'),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
                user_id=current_user.id,
                category_id=int(request.form.get('category_id')) if request.form.get('category_id') else None,
            )
            db.session.add(expense)
            db.session.commit()
            clear_dashboard_cache(current_user.id)
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
        expense.amount      = float(request.form.get('amount'))
        expense.description = request.form.get('description')
        expense.date        = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        cat_id              = request.form.get('category_id') or None
        expense.category_id = int(cat_id) if cat_id else None
        db.session.commit()
        clear_dashboard_cache(current_user.id)
        flash('Expense updated successfully', 'success')
        return redirect(url_for('expenses.index'))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('expenses/edit.html', expense=expense, categories=categories)


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        if _is_fetch(request):
            return jsonify({'error': 'Unauthorized'}), 403
        flash('Unauthorized access', 'error')
        return redirect(url_for('expenses.index'))

    db.session.delete(expense)
    db.session.commit()
    clear_dashboard_cache(current_user.id)

    if _is_fetch(request):
        return jsonify({'success': True})

    flash('Expense deleted successfully', 'success')
    return redirect(url_for('expenses.index'))


@bp.route('/api/recent')
@login_required
def api_recent():
    limit    = request.args.get('limit', 10, type=int)
    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc()).limit(limit).all()
    return jsonify([e.to_dict() for e in expenses])


@bp.route('/api/by-date-range')
@login_required
def api_by_date_range():
    start_date = request.args.get('start')
    end_date   = request.args.get('end')
    query      = Expense.query.filter_by(user_id=current_user.id)
    if start_date:
        query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    return jsonify([e.to_dict() for e in query.order_by(Expense.date.desc()).all()])
