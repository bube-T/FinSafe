# FinSafe - Personal Finance Tracker with Budget Alerts

A comprehensive web application to help you track expenses, categorize spending, and get alerts when approaching budget limits. Built with **Flask** (Python), **SQLite** or **PostgreSQL**, and **Chart.js** for visualizations.

## Features

- **Expense Tracking**: Add, edit, and delete expenses with dates and descriptions
- **Custom Categories**: Create and manage your own spending categories
- **Budget Management**: Set budgets for categories or overall spending with customizable alert thresholds
- **CSV Import**: Import bank statements and transactions from CSV files
- **Spending Trends**: Visualize your spending patterns over the last 6 months
- **Category Breakdown**: See how much you're spending in each category
- **Monthly Reports**: Track your monthly spending with detailed summaries
- **Budget Alerts**: Automatic daily checks for budget threshold alerts (configurable percentage)

## Tech stack

| Layer | Technologies |
|--------|----------------|
| **Runtime** | Python 3.8+ |
| **Web framework** | [Flask](https://flask.palletsprojects.com/) |
| **ORM & database** | [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) / [SQLAlchemy](https://www.sqlalchemy.org/) |
| **Migrations** | [Flask-Migrate](https://flask-migrate.readthedocs.io/) (Alembic) |
| **Authentication** | [Flask-Login](https://flask-login.readthedocs.io/), [Werkzeug](https://werkzeug.palletsprojects.com/) (password hashing) |
| **Database** | **SQLite** by default for local development; **PostgreSQL** supported via `DATABASE_URL` ([psycopg2-binary](https://www.psycopg.org/docs/)) |
| **Configuration** | [python-dotenv](https://pypi.org/project/python-dotenv/) (`.env`) |
| **Email (optional)** | [Flask-Mail](https://pythonhosted.org/Flask-Mail/) for budget alert emails |
| **Scheduled tasks** | [APScheduler](https://apscheduler.readthedocs.io/) (e.g. daily budget checks) |
| **CSV import** | [Pandas](https://pandas.pydata.org/) |
| **PDF reports** | [ReportLab](https://www.reportlab.com/) |
| **Templates & UI** | [Jinja2](https://jinja.palletsprojects.com/), [Bootstrap 5](https://getbootstrap.com/), [Bootstrap Icons](https://icons.getbootstrap.com/) |
| **Charts** | [Chart.js](https://www.chartjs.org/) (loaded from CDN in templates) |

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- PostgreSQL 12+ (optional; recommended for production when not using SQLite)

### Installation

1. **Clone or navigate to the project directory**

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up the database**:
   - **SQLite (default)**: If `DATABASE_URL` is unset, the app uses SQLite (`finance_tracker.db` in the project folder). No server install required.
   - **PostgreSQL (production)**: Create a database and set `DATABASE_URL` in `.env`:
   ```sql
   CREATE DATABASE finance_tracker;
   ```

5. **Configure environment variables** (optional but recommended):
   - Copy `.env.example` to `.env` (or create `.env` manually):
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` and set at least:
     - `SECRET_KEY`: A random secret key for Flask sessions
     - `DATABASE_URL`: Omit or leave unset to use SQLite; or set a PostgreSQL URL, for example:
       ```
       DATABASE_URL=postgresql://username:password@localhost/finance_tracker
       ```
   - For budget **email** alerts, add `MAIL_*` variables (see `PHASE2_ENHANCED.md` or your deployment docs).

6. **Initialize the database**:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

7. **Run the application**:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Usage

### Getting Started

1. **Register an account**: Create a new user account at `/auth/register`
2. **Login**: Access your dashboard at `/auth/login`
3. **Create categories**: Set up spending categories (e.g., Food, Transportation, Entertainment)
4. **Add expenses**: Start tracking your expenses manually or import from CSV
5. **Set budgets**: Create budgets for categories or overall spending with alert thresholds

### CSV Import Format

Your CSV file should have the following columns:
- `date`: Date in format YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY
- `amount`: Expense amount (can include $ and commas)
- `description`: Description of the expense
- `category`: (Optional) Category name - will be created if it doesn't exist

Example CSV:
```csv
date,amount,description,category
2024-01-15,25.50,Grocery Store,Food
2024-01-16,$50.00,Gas Station,Transportation
2024-01-17,15.99,Netflix Subscription,Entertainment
```

### Budget Alerts

- Budget alerts are checked daily at 9 AM
- You'll see alerts on your dashboard when spending reaches your configured threshold (default: 80%)
- Alerts are displayed in real-time on the dashboard
- Budget cards turn red when alert threshold is reached

## Project Structure

```
FinSafe/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── scheduler.py         # Budget alert scheduler
│   ├── routes/              # Route blueprints
│   │   ├── auth.py          # Authentication routes
│   │   ├── expenses.py      # Expense management
│   │   ├── categories.py    # Category management
│   │   ├── budgets.py       # Budget management
│   │   ├── dashboard.py     # Dashboard and analytics
│   │   └── import_csv.py    # CSV import functionality
│   └── templates/           # Jinja2 templates
│       ├── base.html        # Base template
│       ├── auth/            # Auth templates
│       ├── dashboard/       # Dashboard templates
│       ├── expenses/        # Expense templates
│       ├── categories/      # Category templates
│       ├── budgets/         # Budget templates
│       └── import/          # Import templates
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Endpoints

### Dashboard
- `GET /` - Main dashboard
- `GET /api/spending-trends` - 6-month spending trends
- `GET /api/category-breakdown` - Current month category breakdown
- `GET /api/monthly-summary` - Monthly spending summary
- `GET /api/recent-expenses` - Recent expenses list

### Expenses
- `GET /expenses/` - List all expenses
- `GET /expenses/add` - Add expense form
- `POST /expenses/add` - Create expense
- `GET /expenses/edit/<id>` - Edit expense form
- `POST /expenses/edit/<id>` - Update expense
- `POST /expenses/delete/<id>` - Delete expense

### Categories
- `GET /categories/` - List all categories
- `GET /categories/add` - Add category form
- `POST /categories/add` - Create category
- `GET /categories/edit/<id>` - Edit category form
- `POST /categories/edit/<id>` - Update category
- `POST /categories/delete/<id>` - Delete category

### Budgets
- `GET /budgets/` - List all budgets
- `GET /budgets/add` - Add budget form
- `POST /budgets/add` - Create budget
- `GET /budgets/edit/<id>` - Edit budget form
- `POST /budgets/edit/<id>` - Update budget
- `POST /budgets/delete/<id>` - Delete budget

### Import
- `GET /import/` - CSV import form
- `POST /import/` - Process CSV import

## Development

### Running in Development Mode

```bash
python run.py
```

The app runs in debug mode by default. For production, set `debug=False` in `run.py` and use a proper WSGI server like Gunicorn.

### Database Migrations

When you modify models:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Future Enhancements

- Email notifications for budget alerts
- Export expenses to CSV/PDF
- Recurring expense tracking
- Multi-currency support
- Mobile app
- Bank account integration via APIs

## License

This project is open source and available for personal use.

