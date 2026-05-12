from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta, date
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    incomes = db.relationship('Income', backref='user', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    savings_goals = db.relationship('SavingsGoal', backref='user', lazy=True, cascade='all, delete-orphan')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    color = db.Column(db.String(7), default='#6c757d')  # Hex color code
    is_default = db.Column(db.Boolean, default=False)  # True for default categories
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='category', lazy=True)
    budgets = db.relationship('Budget', backref='category', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('name', 'user_id', name='unique_category_user'),)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'description': self.description,
            'date': self.date.isoformat(),
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Uncategorized'
        }

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(100), nullable=True)  # e.g., Salary, Freelance, Investment
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'description': self.description,
            'date': self.date.isoformat(),
            'source': self.source
        }

class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    current_amount = db.Column(db.Numeric(10, 2), default=0.0)
    target_date = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_progress_percentage(self):
        """Get percentage progress towards goal"""
        if self.target_amount == 0:
            return 0
        return min((float(self.current_amount) / float(self.target_amount)) * 100, 100)
    
    def get_remaining_amount(self):
        """Get remaining amount to reach goal"""
        return max(float(self.target_amount) - float(self.current_amount), 0)
    
    def is_completed(self):
        """Check if goal is completed"""
        return float(self.current_amount) >= float(self.target_amount)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'target_amount': float(self.target_amount),
            'current_amount': float(self.current_amount),
            'remaining': self.get_remaining_amount(),
            'progress': round(self.get_progress_percentage(), 2),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_completed': self.is_completed()
        }

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    period = db.Column(db.String(20), nullable=False)  # 'monthly', 'weekly', 'yearly'
    month = db.Column(db.Integer, nullable=True)  # For monthly budgets (1-12)
    year = db.Column(db.Integer, nullable=True)  # For monthly budgets
    alert_threshold = db.Column(db.Numeric(5, 2), default=80.0)  # Percentage (e.g., 80%)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_current_spending(self):
        """Calculate current spending for this budget period"""
        today = date.today()
        
        if self.period == 'monthly':
            start_date = date(today.year, today.month, 1)
            end_date = today
        elif self.period == 'weekly':
            days_since_monday = today.weekday()
            start_date = today - timedelta(days=days_since_monday)
            end_date = today
        elif self.period == 'yearly':
            start_date = date(today.year, 1, 1)
            end_date = today
        else:
            return 0
        
        query = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == self.user_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        )
        
        if self.category_id:
            query = query.filter(Expense.category_id == self.category_id)
        
        result = query.scalar()
        return float(result) if result else 0.0
    
    def get_percentage_used(self):
        """Get percentage of budget used"""
        spending = self.get_current_spending()
        if self.amount == 0:
            return 0
        return (spending / float(self.amount)) * 100
    
    def is_alert_threshold_reached(self):
        """Check if alert threshold has been reached"""
        return self.get_percentage_used() >= self.alert_threshold
    
    def to_dict(self):
        spending = self.get_current_spending()
        percentage = self.get_percentage_used()
        return {
            'id': self.id,
            'amount': float(self.amount),
            'spending': spending,
            'remaining': float(self.amount) - spending,
            'percentage': round(percentage, 2),
            'period': self.period,
            'alert_threshold': float(self.alert_threshold),
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'All Categories',
            'alert_reached': percentage >= float(self.alert_threshold)
        }

