import os
from datetime import datetime
from flask import Flask
from app.config import config
from app.extensions import db, migrate, login_manager, csrf
from flask_apscheduler import APScheduler
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

scheduler = APScheduler()


def ensure_review_columns(app):
    """Ensure the reviews table has all required columns in SQLite."""
    if not app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite:'):
        return

    with app.app_context():
        try:
            result = db.session.execute(text("PRAGMA table_info('reviews')")).fetchall()
            columns = {row[1] for row in result}
            migrations = [
                ('is_flagged', 'ALTER TABLE reviews ADD COLUMN is_flagged BOOLEAN NOT NULL DEFAULT 0'),
                ('operator_response', 'ALTER TABLE reviews ADD COLUMN operator_response TEXT'),
                ('operator_responded_at', 'ALTER TABLE reviews ADD COLUMN operator_responded_at DATETIME'),
            ]
            for col, sql in migrations:
                if col not in columns:
                    db.session.execute(text(sql))
            db.session.commit()
        except OperationalError:
            db.session.rollback()
            pass


def create_app(config_name=None):
    """Application factory for Devine Adventures."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # APScheduler — only start if not already running (avoids double-start in reloader)
    app.config['SCHEDULER_API_ENABLED'] = False
    app.config['SCHEDULER_TIMEZONE'] = 'Africa/Nairobi'
    scheduler.init_app(app)
    if not scheduler.running:
        scheduler.start()

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return db.session.get(User, int(user_id))

    # Context processor — inject globals into all templates
    @app.context_processor
    def inject_globals():
        return {
            'site_name': 'Devine Adventures',
            'current_year': datetime.now().year,
        }

    # Register blueprints
    from app.routes import main_bp
    from app.routes.bookings import bookings_bp
    from app.routes.operator import operator_bp
    from app.routes.payments import payments_bp
    from app.routes.admin import admin_bp
    from app.routes.reviews import reviews_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(operator_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reviews_bp)

    # Create tables in development and ensure schema updates for old SQLite databases
    with app.app_context():
        from app import models  # noqa: F401 — ensure models are imported
        db.create_all()
        ensure_review_columns(app)

    # Register scheduled jobs
    from app.utils.scheduler import run_review_request_job
    if not scheduler.get_job('review_requests'):
        scheduler.add_job(
            id='review_requests',
            func=run_review_request_job,
            args=[app],
            trigger='cron',
            hour=8,
            minute=0,
            replace_existing=True
        )

    return app
