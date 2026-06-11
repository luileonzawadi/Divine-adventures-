from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    """User model supporting multiple roles: traveler, operator, admin."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(500))
    role = db.Column(
        db.Enum('traveler', 'operator', 'admin', name='user_role'),
        default='traveler',
        nullable=False
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    operator_profile = db.relationship(
        'TourOperator', back_populates='user', uselist=False, cascade='all, delete-orphan'
    )
    bookings = db.relationship(
        'Booking', back_populates='user', lazy='dynamic', cascade='all, delete-orphan'
    )
    reviews = db.relationship(
        'Review', back_populates='user', lazy='dynamic', cascade='all, delete-orphan'
    )

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        """Return the user's full name."""
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_operator(self):
        return self.role == 'operator'

    @property
    def is_traveler(self):
        return self.role == 'traveler'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class TourOperator(db.Model):
    """Tour operator profile linked to a user account."""
    __tablename__ = 'tour_operators'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True, nullable=False
    )
    company_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    license_number = db.Column(db.String(100))
    location = db.Column(db.String(200))
    website = db.Column(db.String(300))
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    total_tours = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user = db.relationship('User', back_populates='operator_profile')
    tours = db.relationship(
        'Tour', back_populates='operator', lazy='dynamic', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<TourOperator {self.company_name}>'
