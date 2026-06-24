import os
from datetime import datetime
from flask import Flask
from app.config import config
from app.extensions import db, migrate, login_manager, csrf
from flask_apscheduler import APScheduler
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

scheduler = APScheduler()


def auto_seed(app):
    """Create default accounts on first deploy if the database is empty."""
    with app.app_context():
        try:
            from app.models.user import User, TourOperator
            if User.query.first():
                return  # already seeded — do nothing

            print("[auto_seed] No users found — seeding default accounts...")

            # Admin
            admin = User(
                email='admin@devine.com', username='admin',
                first_name='Admin', last_name='Boss',
                phone='+254733333333', role='admin'
            )
            admin.set_password('password')
            db.session.add(admin)

            # Operator user
            operator_user = User(
                email='operator@devine.com', username='operator',
                first_name='Alice', last_name='Operator',
                phone='+254722222222', role='operator'
            )
            operator_user.set_password('password')
            db.session.add(operator_user)
            db.session.flush()

            # Operator profile
            op_profile = TourOperator(
                user_id=operator_user.id,
                company_name='Devine Adventure Guides',
                description='Professional local guides and trekking experts in Kenya.',
                license_number='OP-294029',
                location='Nairobi, Kenya',
                website='www.devineadventures.co.ke',
                is_verified=True,
                rating=4.9,
                total_tours=0
            )
            db.session.add(op_profile)

            # Default traveler
            traveler = User(
                email='traveler@devine.com', username='traveler',
                first_name='John', last_name='Traveler',
                phone='+254712345678', role='traveler'
            )
            traveler.set_password('password')
            db.session.add(traveler)

            db.session.commit()
            print("[auto_seed] Done! Default accounts created.")
            print("[auto_seed]   admin@devine.com    / password")
            print("[auto_seed]   operator@devine.com / password")
            print("[auto_seed]   traveler@devine.com / password")
        except Exception as e:
            db.session.rollback()
            print(f"[auto_seed] Skipped: {e}")


def ensure_review_columns(app):
    """Ensure all tables have required columns in SQLite."""
    if not app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite:'):
        return

    with app.app_context():
        try:
            # reviews table
            result = db.session.execute(text("PRAGMA table_info('reviews')")).fetchall()
            columns = {row[1] for row in result}
            for col, sql in [
                ('is_flagged', 'ALTER TABLE reviews ADD COLUMN is_flagged BOOLEAN NOT NULL DEFAULT 0'),
                ('operator_response', 'ALTER TABLE reviews ADD COLUMN operator_response TEXT'),
                ('operator_responded_at', 'ALTER TABLE reviews ADD COLUMN operator_responded_at DATETIME'),
            ]:
                if col not in columns:
                    db.session.execute(text(sql))

            # bookings table
            result = db.session.execute(text("PRAGMA table_info('bookings')")).fetchall()
            columns = {row[1] for row in result}
            for col, sql in [
                ('review_request_sent', 'ALTER TABLE bookings ADD COLUMN review_request_sent BOOLEAN NOT NULL DEFAULT 0'),
            ]:
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

    # Create tables and auto-seed default accounts if DB is empty
    with app.app_context():
        from app import models  # noqa: F401 — ensure models are imported
        db.create_all()
        ensure_review_columns(app)
        auto_seed(app)

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
