from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Category

bp = Blueprint('categories', __name__, url_prefix='/categories')

@bp.route('/')
@login_required
def index():
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    return render_template('categories/index.html', categories=categories)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        
        if not name:
            flash('Category name is required', 'error')
            return render_template('categories/add.html')
        
        # Check if category already exists for this user
        existing = Category.query.filter_by(user_id=current_user.id, name=name).first()
        if existing:
            flash('Category already exists', 'error')
            return render_template('categories/add.html')
        
        category = Category(name=name, user_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully', 'success')
        return redirect(url_for('categories.index'))
    
    return render_template('categories/add.html')

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.get_or_404(id)
    
    if category.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('categories.index'))
    
    if request.method == 'POST':
        name = request.form.get('name').strip()
        
        if not name:
            flash('Category name is required', 'error')
            return render_template('categories/edit.html', category=category)
        
        # Check if another category with same name exists
        existing = Category.query.filter_by(user_id=current_user.id, name=name).first()
        if existing and existing.id != category.id:
            flash('Category name already exists', 'error')
            return render_template('categories/edit.html', category=category)
        
        category.name = name
        db.session.commit()
        flash('Category updated successfully', 'success')
        return redirect(url_for('categories.index'))
    
    return render_template('categories/edit.html', category=category)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.get_or_404(id)
    
    if category.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('categories.index'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully', 'success')
    return redirect(url_for('categories.index'))

@bp.route('/api/list')
@login_required
def api_list():
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

