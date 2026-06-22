from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_compress import Compress
from flask_caching import Cache
import os
from dotenv import load_dotenv

load_dotenv()

db           = SQLAlchemy()
login_manager = LoginManager()
migrate      = Migrate()
mail         = Mail()
compress     = Compress()
cache        = Cache()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        database_url = 'sqlite:///finance_tracker.db'
    # Railway provides postgres:// but SQLAlchemy requires postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Flask-Mail
    app.config['MAIL_SERVER']         = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT']           = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS']        = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME']       = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD']       = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@finsafe.com')

    # Gzip compression for JSON/text responses ≥ 1 KB
    # Already-compressed types (image/*, video/*, application/zip, etc.) are skipped automatically.
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html', 'text/css', 'text/javascript',
        'application/json', 'application/javascript',
    ]
    app.config['COMPRESS_MIN_SIZE'] = 1024   # bytes; skip tiny responses
    app.config['COMPRESS_LEVEL']    = 6      # gzip level 1-9, 6 is balanced

    # Per-process in-memory cache; per-user keys with short TTL
    app.config['CACHE_TYPE']            = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 120   # seconds

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)
    mail.init_app(app)
    compress.init_app(app)
    cache.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import auth, expenses, categories, budgets, dashboard, import_csv, reports, income, savings_goals, settings
    app.register_blueprint(auth.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(income.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(budgets.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(import_csv.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(savings_goals.bp)
    app.register_blueprint(settings.bp)

    from app.scheduler import init_scheduler
    init_scheduler(app)

    return app
