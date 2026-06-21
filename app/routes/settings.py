from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Budget, Expense, Income, SavingsGoal, Category

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/')
@login_required
def index():
    expense_count  = Expense.query.filter_by(user_id=current_user.id).count()
    income_count   = Income.query.filter_by(user_id=current_user.id).count()
    budget_count   = Budget.query.filter_by(user_id=current_user.id).count()
    goal_count     = SavingsGoal.query.filter_by(user_id=current_user.id).count()
    category_count = Category.query.filter_by(user_id=current_user.id).count()

    return render_template('settings/index.html',
                           expense_count=expense_count,
                           income_count=income_count,
                           budget_count=budget_count,
                           goal_count=goal_count,
                           category_count=category_count)
