from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage: hero section + featured reviews with photos."""
    from app.models import Review, ReviewPhoto, Tour

    # Top-rated approved reviews that have at least one photo
    featured_reviews = (
        Review.query
        .join(ReviewPhoto, Review.id == ReviewPhoto.review_id)
        .filter(Review.is_approved == True, Review.rating >= 4)
        .order_by(Review.rating.desc(), Review.created_at.desc())
        .distinct()
        .limit(6)
        .all()
    )

    # Featured / active tours for homepage grid
    featured_tours = (
        Tour.query
        .filter_by(is_active=True, is_featured=True)
        .limit(6)
        .all()
    )

    return render_template(
        'index.html',
        featured_reviews=featured_reviews,
        featured_tours=featured_tours
    )


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    from app.models import User
    from app.extensions import db

    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'operator':
                return redirect(url_for('operator.dashboard'))
            else:
                return redirect(url_for('bookings.dashboard'))
        flash("Invalid email or password.", "danger")

    return render_template('auth/login.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """New user registration."""
    from app.models import User
    from app.extensions import db

    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', 'traveler')

        errors = []
        if not all([first_name, last_name, username, email, password]):
            errors.append("All fields are required.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if role not in ('traveler', 'operator'):
            role = 'traveler'

        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template('auth/register.html')

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Welcome to Devine Adventures, {first_name}! 🎉", "success")
        if user.role == 'operator':
            return redirect(url_for('operator.dashboard'))
        return redirect(url_for('bookings.dashboard'))

    return render_template('auth/register.html')


@main_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash("You've been logged out. See you next adventure! 👋", "info")
    return redirect(url_for('main.index'))


@main_bp.route('/contact', methods=['POST'])
def contact():
    """Handle contact form submission."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()

    if not all([name, email, message]):
        flash("Please fill in all fields.", "warning")
    else:
        # TODO: hook up email sending via send_contact_email()
        flash(f"Thanks {name}! We'll get back to you within 24 hours. ✉️", "success")

    return redirect(url_for('main.index') + '#contact')

@main_bp.route('/tours/<slug>')
def tour_detail(slug):
    """Tour detail page with itinerary, dates, and verified reviews."""
    from app.models import Tour, TourDate, Review

    tour = Tour.query.filter_by(slug=slug, is_active=True).first_or_404()
    active_dates = tour.dates.filter_by(is_active=True).order_by(TourDate.start_date).all()
    itinerary = tour.itinerary_days.order_by('day_number').all()
    approved_reviews = (
        Review.query
        .filter_by(tour_id=tour.id, is_approved=True)
        .order_by(Review.created_at.desc())
        .all()
    )

    avg_rating = 0.0
    if approved_reviews:
        avg_rating = round(sum(r.rating for r in approved_reviews) / len(approved_reviews), 1)

    return render_template(
        'tour_detail.html',
        tour=tour,
        active_dates=active_dates,
        itinerary=itinerary,
        reviews=approved_reviews,
        avg_rating=avg_rating,
        review_count=len(approved_reviews)
    )

