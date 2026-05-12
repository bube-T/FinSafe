from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category
from datetime import datetime
import pandas as pd
import io

bp = Blueprint('import_csv', __name__, url_prefix='/import')

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return render_template('import/index.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return render_template('import/index.html')
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'error')
            return render_template('import/index.html')
        
        try:
            # Read CSV file
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            df = pd.read_csv(stream)
            
            # Expected columns: date, amount, description, category (optional)
            required_columns = ['date', 'amount', 'description']
            
            # Check if required columns exist (case-insensitive)
            df.columns = df.columns.str.strip().str.lower()
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                return render_template('import/index.html')
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Parse date (try multiple formats)
                    date_str = str(row['date']).strip()
                    date_obj = None
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if not date_obj:
                        errors.append(f'Row {index + 2}: Invalid date format: {date_str}')
                        continue
                    
                    # Parse amount (handle negative values and currency symbols)
                    amount_str = str(row['amount']).strip()
                    amount_str = amount_str.replace('£', '').replace('$', '').replace(',', '').strip()
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        errors.append(f'Row {index + 2}: Invalid amount: {amount_str}')
                        continue
                    
                    description = str(row['description']).strip() if pd.notna(row.get('description')) else 'Imported transaction'
                    
                    # Handle category if provided
                    category_id = None
                    if 'category' in df.columns and pd.notna(row.get('category')):
                        category_name = str(row['category']).strip()
                        category = Category.query.filter_by(
                            user_id=current_user.id,
                            name=category_name
                        ).first()
                        
                        if not category:
                            # Create category if it doesn't exist
                            category = Category(name=category_name, user_id=current_user.id)
                            db.session.add(category)
                            db.session.flush()
                        
                        category_id = category.id
                    
                    # Check if expense already exists (avoid duplicates)
                    existing = Expense.query.filter_by(
                        user_id=current_user.id,
                        amount=amount,
                        date=date_obj,
                        description=description
                    ).first()
                    
                    if not existing:
                        expense = Expense(
                            amount=amount,
                            description=description,
                            date=date_obj,
                            user_id=current_user.id,
                            category_id=category_id
                        )
                        db.session.add(expense)
                        imported_count += 1
                
                except Exception as e:
                    errors.append(f'Row {index + 2}: {str(e)}')
                    continue
            
            db.session.commit()
            
            if imported_count > 0:
                flash(f'Successfully imported {imported_count} expenses', 'success')
            if errors:
                flash(f'Encountered {len(errors)} errors during import', 'warning')
            
            return redirect(url_for('expenses.index'))
        
        except Exception as e:
            flash(f'Error processing CSV file: {str(e)}', 'error')
            return render_template('import/index.html')
    
    return render_template('import/index.html')

