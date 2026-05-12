# Database Setup Guide

## ✅ What We Just Did

I've set up your database step by step. Here's what happened:

### Step 1: Created `.env` file
- Added `SECRET_KEY` for Flask session security
- Set `DATABASE_URL` to use SQLite (`sqlite:///finance_tracker.db`)
- SQLite is perfect for development - no server needed!

### Step 2: Updated App Configuration
- Modified `app/__init__.py` to use SQLite by default
- Still supports PostgreSQL if you set `DATABASE_URL` in `.env`

### Step 3: Initialized Flask-Migrate
```bash
flask db init
```
- Created `migrations/` directory
- Set up Alembic for database version control

### Step 4: Created Initial Migration
```bash
flask db migrate -m "Initial migration"
```
- Analyzed your models (User, Category, Expense, Budget)
- Generated migration file with all table definitions
- Migration file: `migrations/versions/d7de7bcf51d2_initial_migration_...py`

### Step 5: Applied Migration
```bash
flask db upgrade
```
- Created the database file: `finance_tracker.db`
- Created all tables:
  - `user` - User accounts
  - `category` - Spending categories (with color and is_default)
  - `expense` - Transaction records
  - `budget` - Budget settings (with month/year tracking)

## Database Structure

### User Table
- id, username, email, password_hash, created_at

### Category Table
- id, name, user_id, color, is_default, created_at
- Unique constraint: (name, user_id)

### Expense Table
- id, amount, description, date, user_id, category_id, created_at

### Budget Table
- id, amount, period, month, year, alert_threshold, user_id, category_id, created_at, updated_at

## Your Database is Ready! 🎉

The database file (`finance_tracker.db`) will be created automatically when you first run the app.

## Next Steps

1. **Run the application:**
   ```bash
   python run.py
   ```

2. **Access the app:**
   - Open browser to: `http://localhost:5000`
   - Register a new user
   - Default categories will be created automatically!

## Switching to PostgreSQL (Optional)

If you want to use PostgreSQL instead of SQLite:

1. Install PostgreSQL on your machine
2. Create a database:
   ```sql
   CREATE DATABASE finance_tracker;
   ```

3. Update `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost/finance_tracker
   ```

4. Run migrations again:
   ```bash
   flask db upgrade
   ```

## Future Migrations

When you modify models, create new migrations:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Troubleshooting

- **Database locked error**: Close any other connections to the database
- **Migration conflicts**: Check `flask db current` to see current version
- **Reset database**: Delete `finance_tracker.db` and run `flask db upgrade` again

