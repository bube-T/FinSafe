"""Utility functions for the FinSafe app"""

from app import db
from app.models import Category

# Default categories with colors for Phase 1 MVP
DEFAULT_CATEGORIES = [
    {'name': 'Food', 'color': '#28a745'},  # Green
    {'name': 'Transport', 'color': '#007bff'},  # Blue
    {'name': 'Bills', 'color': '#dc3545'},  # Red
    {'name': 'Entertainment', 'color': '#ffc107'},  # Yellow
    {'name': 'Shopping', 'color': '#6f42c1'},  # Purple
    {'name': 'Other', 'color': '#6c757d'},  # Gray
]

def create_default_categories(user_id):
    """Create default categories for a new user"""
    categories = []
    for cat_data in DEFAULT_CATEGORIES:
        category = Category(
            name=cat_data['name'],
            user_id=user_id,
            color=cat_data['color'],
            is_default=True
        )
        categories.append(category)
        db.session.add(category)
    
    db.session.commit()
    return categories

