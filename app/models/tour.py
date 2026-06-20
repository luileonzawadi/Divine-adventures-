import re
from datetime import datetime, timezone
from app.extensions import db


class Tour(db.Model):
    """Adventure tour listing with full details."""
    __tablename__ = 'tours'

    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(
        db.Integer, db.ForeignKey('tour_operators.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(500))
    duration_days = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(
        db.Enum('easy', 'moderate', 'hard', 'extreme', name='difficulty_level'),
        nullable=False
    )
    max_group_size = db.Column(db.Integer, nullable=False)
    price_kes = db.Column(db.Numeric(10, 2), nullable=False)
    price_usd = db.Column(db.Numeric(10, 2), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    meeting_point = db.Column(db.String(300))
    category = db.Column(
        db.Enum(
            'hiking', 'safari', 'mountain_climbing', 'water_sports',
            'cultural', 'camping', 'cycling', 'wildlife', 'photography',
            name='tour_category'
        ),
        nullable=False
    )
    included_items = db.Column(db.Text)  # Newline-separated list
    excluded_items = db.Column(db.Text)  # Newline-separated list
    cover_image_url = db.Column(db.String(500))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deposit_percent = db.Column(db.Integer, default=100, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    operator = db.relationship('TourOperator', back_populates='tours')
    dates = db.relationship(
        'TourDate', back_populates='tour', lazy='dynamic',
        cascade='all, delete-orphan', order_by='TourDate.start_date'
    )
    images = db.relationship(
        'TourImage', back_populates='tour', lazy='dynamic',
        cascade='all, delete-orphan', order_by='TourImage.sort_order'
    )
    itinerary_days = db.relationship(
        'Itinerary', back_populates='tour', lazy='dynamic',
        cascade='all, delete-orphan', order_by='Itinerary.day_number'
    )
    bookings = db.relationship(
        'Booking', back_populates='tour', lazy='dynamic', cascade='all, delete-orphan'
    )
    reviews = db.relationship(
        'Review', back_populates='tour', lazy='dynamic', cascade='all, delete-orphan'
    )

    @staticmethod
    def generate_slug(title):
        """Generate a URL-friendly slug from the tour title."""
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    @property
    def average_rating(self):
        """Calculate average review rating."""
        reviews = self.reviews.all()
        if not reviews:
            return 0.0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def total_reviews(self):
        """Count total approved reviews."""
        return self.reviews.filter_by(is_approved=True).count()

    @property
    def included_list(self):
        """Return included items as a list."""
        if not self.included_items:
            return []
        return [item.strip() for item in self.included_items.split('\n') if item.strip()]

    @property
    def excluded_list(self):
        """Return excluded items as a list."""
        if not self.excluded_items:
            return []
        return [item.strip() for item in self.excluded_items.split('\n') if item.strip()]

    @property
    def difficulty_color(self):
        """Return CSS color class for difficulty level."""
        colors = {
            'easy': 'badge--easy',
            'moderate': 'badge--moderate',
            'hard': 'badge--hard',
            'extreme': 'badge--extreme'
        }
        return colors.get(self.difficulty, 'badge--easy')

    def __repr__(self):
        return f'<Tour {self.title}>'


class TourDate(db.Model):
    """Available dates for a tour."""
    __tablename__ = 'tour_dates'

    id = db.Column(db.Integer, primary_key=True)
    tour_id = db.Column(
        db.Integer, db.ForeignKey('tours.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    max_capacity = db.Column(db.Integer, default=20, nullable=False)
    current_bookings = db.Column(db.Integer, default=0, nullable=False)
    price_override_kes = db.Column(db.Numeric(10, 2))  # Seasonal pricing
    price_override_usd = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    tour = db.relationship('Tour', back_populates='dates')
    bookings = db.relationship(
        'Booking', back_populates='tour_date', lazy='dynamic'
    )
    waitlist_entries = db.relationship(
        'Waitlist', back_populates='tour_date', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def spots_available(self):
        """Dynamically compute spots available."""
        return max(0, self.max_capacity - self.current_bookings)

    @property
    def is_sold_out(self):
        """Check if all spots are taken."""
        return self.spots_available <= 0

    @property
    def effective_price_kes(self):
        """Return override price or fall back to tour base price."""
        return self.price_override_kes or self.tour.price_kes

    @property
    def effective_price_usd(self):
        """Return override price or fall back to tour base price."""
        return self.price_override_usd or self.tour.price_usd

    def __repr__(self):
        return f'<TourDate {self.tour_id} {self.start_date} - {self.end_date}>'


class TourImage(db.Model):
    """Gallery images for a tour."""
    __tablename__ = 'tour_images'

    id = db.Column(db.Integer, primary_key=True)
    tour_id = db.Column(
        db.Integer, db.ForeignKey('tours.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    image_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(300))
    is_cover = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    # Relationships
    tour = db.relationship('Tour', back_populates='images')

    def __repr__(self):
        return f'<TourImage {self.tour_id} #{self.sort_order}>'


class CommunityPhoto(db.Model):
    """Photos displayed in the community gallery section on the homepage."""
    __tablename__ = 'community_photos'

    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<CommunityPhoto {self.id}>'


class ShopItem(db.Model):
    """Products displayed in the Devine Shop section on the homepage."""
    __tablename__ = 'shop_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price_kes = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    image_url = db.Column(db.String(500))
    buy_link = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<ShopItem {self.name}>'


class Itinerary(db.Model):
    """Day-by-day tour itinerary."""
    __tablename__ = 'itineraries'

    id = db.Column(db.Integer, primary_key=True)
    tour_id = db.Column(
        db.Integer, db.ForeignKey('tours.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    day_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    highlights = db.Column(db.Text)  # Comma-separated
    accommodation = db.Column(db.String(200))
    meals_included = db.Column(db.String(100))  # e.g., "B, L, D"

    # Relationships
    tour = db.relationship('Tour', back_populates='itinerary_days')

    @property
    def highlights_list(self):
        """Return highlights as a list."""
        if not self.highlights:
            return []
        return [h.strip() for h in self.highlights.split(',') if h.strip()]

    def __repr__(self):
        return f'<Itinerary Day {self.day_number}: {self.title}>'
