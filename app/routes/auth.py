from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from app.utils import create_default_categories

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.flush()
        create_default_categories(user.id)
        db.session.commit()

        flash('Registration successful! Default categories have been created. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username', '').strip()
    email    = request.form.get('email', '').strip()

    if not username or not email:
        flash('Username and email are required.', 'error')
        return redirect(url_for('settings.index'))

    if User.query.filter(User.username == username, User.id != current_user.id).first():
        flash('That username is already taken.', 'error')
        return redirect(url_for('settings.index'))

    if User.query.filter(User.email == email, User.id != current_user.id).first():
        flash('That email is already in use.', 'error')
        return redirect(url_for('settings.index'))

    current_user.username = username
    current_user.email    = email
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('settings.index'))

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_pw  = request.form.get('current_password', '')
    new_pw      = request.form.get('new_password', '')
    confirm_pw  = request.form.get('confirm_password', '')

    if not check_password_hash(current_user.password_hash, current_pw):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('settings.index'))

    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('settings.index'))

    if len(new_pw) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return redirect(url_for('settings.index'))

    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return redirect(url_for('settings.index'))

@bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password', '')

    if not check_password_hash(current_user.password_hash, password):
        flash('Incorrect password — account not deleted.', 'error')
        return redirect(url_for('settings.index'))

    user = current_user._get_current_object()
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Your account and all data have been permanently deleted.', 'info')
    return redirect(url_for('auth.login'))
