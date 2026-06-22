from app import db, cache
from app.models import Category

DEFAULT_CATEGORIES = [
    {'name': 'Food',          'color': '#28a745'},
    {'name': 'Transport',     'color': '#007bff'},
    {'name': 'Bills',         'color': '#dc3545'},
    {'name': 'Entertainment', 'color': '#ffc107'},
    {'name': 'Shopping',      'color': '#6f42c1'},
    {'name': 'Other',         'color': '#6c757d'},
]

def create_default_categories(user_id):
    """Bulk-insert default categories for a new user in a single round-trip."""
    categories = [
        Category(name=c['name'], user_id=user_id, color=c['color'], is_default=True)
        for c in DEFAULT_CATEGORIES
    ]
    db.session.add_all(categories)
    # caller is responsible for commit (auth.register flushes then commits)
    return categories

def clear_dashboard_cache(user_id):
    """Invalidate all cached dashboard API responses for this user."""
    for suffix in ('spending_trends', 'category_breakdown', 'monthly_summary',
                   'savings_goals_summary', 'recent_expenses', 'net_worth', 'notifications'):
        cache.delete(f'u{user_id}_{suffix}')
