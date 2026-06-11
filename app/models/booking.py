import random
import string
from datetime import datetime, timezone
from app.extensions import db


class Booking(db.Model):
    """Tour booking record."""
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    tour_id = db.Column(
        db.Integer, db.ForeignKey('tours.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    tour_date_id = db.Column(
        db.Integer, db.ForeignKey('tour_dates.id', ondelete='SET NULL'),
        nullable=True
    )
    num_guests = db.Column(db.Integer, nullable=False, default=1)
    total_price_kes = db.Column(db.Numeric(10, 2), nullable=False)
    total_price_usd = db.Column(db.Numeric(10, 2), nullable=False)
    deposit_paid_kes = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    deposit_paid_usd = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    status = db.Column(
        db.Enum('pending_payment', 'pending', 'confirmed', 'cancelled', 'completed', name='booking_status'),
        default='pending_payment', nullable=False
    )
    
    # Traveler Info
    traveler_name = db.Column(db.String(120), nullable=False)
    traveler_email = db.Column(db.String(120), nullable=False)
    traveler_phone = db.Column(db.String(20), nullable=False)
    traveler_nationality = db.Column(db.String(80), nullable=False)
    emergency_contact_name = db.Column(db.String(120), nullable=False)
    emergency_contact_phone = db.Column(db.String(20), nullable=False)
    
    # Review tracking
    review_request_sent = db.Column(db.Boolean, default=False, nullable=False)

    # Check-in Status
    is_checked_in = db.Column(db.Boolean, default=False, nullable=False)
    checked_in_at = db.Column(db.DateTime, nullable=True)

    special_requests = db.Column(db.Text)
    booking_reference = db.Column(
        db.String(20), unique=True, nullable=False, index=True
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', back_populates='bookings')
    tour = db.relationship('Tour', back_populates='bookings')
    tour_date = db.relationship('TourDate', back_populates='bookings')
    payments = db.relationship('Payment', back_populates='booking', cascade='all, delete-orphan')

    @staticmethod
    def generate_reference():
        """Generate a unique booking reference like DA-XXXX-XXXX."""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        part1 = ''.join(random.choices(chars, k=4))
        part2 = ''.join(random.choices(chars, k=4))
        return f'DA-{part1}-{part2}'

    @property
    def is_cancellable(self):
        """Check if booking can still be cancelled."""
        return self.status in ('pending_payment', 'pending', 'confirmed')

    @property
    def deposit_amount_kes(self):
        """Calculate the deposit amount based on the tour config."""
        percent = self.tour.deposit_percent if (self.tour and self.tour.deposit_percent is not None) else 100
        return (self.total_price_kes * percent) / 100

    @property
    def deposit_amount_usd(self):
        """Calculate the deposit amount based on the tour config."""
        percent = self.tour.deposit_percent if (self.tour and self.tour.deposit_percent is not None) else 100
        return (self.total_price_usd * percent) / 100

    @property
    def balance_due_kes(self):
        """Calculate the remaining KES balance due."""
        return self.total_price_kes - (self.deposit_paid_kes or 0)

    @property
    def balance_due_usd(self):
        """Calculate the remaining USD balance due."""
        return self.total_price_usd - (self.deposit_paid_usd or 0)

    @property
    def status_color(self):
        """Return CSS class for booking status."""
        colors = {
            'pending_payment': 'status--pending',
            'pending': 'status--pending',
            'confirmed': 'status--confirmed',
            'cancelled': 'status--cancelled',
            'completed': 'status--completed'
        }
        return colors.get(self.status, 'status--pending')

    def __repr__(self):
        return f'<Booking {self.booking_reference} ({self.status})>'


class Waitlist(db.Model):
    """Waitlist registrations for sold out tour dates."""
    __tablename__ = 'waitlists'

    id = db.Column(db.Integer, primary_key=True)
    tour_date_id = db.Column(
        db.Integer, db.ForeignKey('tour_dates.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True, index=True
    )
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    is_notified = db.Column(db.Boolean, default=False, nullable=False)
    notified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    tour_date = db.relationship('TourDate', back_populates='waitlist_entries')
    user = db.relationship('User')

    def __repr__(self):
        return f'<Waitlist {self.email} -> TourDate {self.tour_date_id}>'


class Review(db.Model):
    """Tour review by a traveler."""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    tour_id = db.Column(
        db.Integer, db.ForeignKey('tours.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    booking_id = db.Column(
        db.Integer, db.ForeignKey('bookings.id', ondelete='SET NULL'),
        nullable=True
    )
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=True, nullable=False)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)
    operator_response = db.Column(db.Text, nullable=True)
    operator_responded_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user = db.relationship('User', back_populates='reviews')
    tour = db.relationship('Tour', back_populates='reviews')
    photos = db.relationship(
        'ReviewPhoto', back_populates='review',
        cascade='all, delete-orphan', lazy='dynamic'
    )

    # Unique constraint: one review per user per tour
    __table_args__ = (
        db.UniqueConstraint('user_id', 'tour_id', name='uq_user_tour_review'),
    )

    @property
    def star_display(self):
        """Return filled and empty star characters."""
        return '★' * self.rating + '☆' * (5 - self.rating)

    @property
    def is_verified(self):
        """Check if review is backed by a completed booking."""
        return self.booking_id is not None

    def __repr__(self):
        return f'<Review {self.user_id} -> Tour {self.tour_id} ({self.rating}★)>'


class Payment(db.Model):
    """Payment transaction record for a booking."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    method = db.Column(db.String(20), nullable=False)  # 'mpesa' or 'stripe'
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'completed', 'failed'
    reference = db.Column(db.String(100), unique=True, nullable=True)  # M-Pesa receipt code or Stripe checkout session ID / payment intent ID.
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationship back to Booking
    booking = db.relationship('Booking', back_populates='payments')

    def __repr__(self):
        return f'<Payment {self.id} for Booking {self.booking_id} ({self.status})>'


class ReviewPhoto(db.Model):
    """Trip photo attached to a traveler review."""
    __tablename__ = 'review_photos'

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(
        db.Integer, db.ForeignKey('reviews.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    image_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    review = db.relationship('Review', back_populates='photos')

    def __repr__(self):
        return f'<ReviewPhoto {self.id} for Review {self.review_id}>'
