import os
import json
import logging
import cloudinary
import cloudinary.uploader
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Payment, Booking, Tour, TourImage
from app.models.user import User, TourOperator
from app.extensions import db

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)
EXCHANGE_RATE = 130.0


def admin_required():
    if current_user.role != 'admin':
        abort(403)


def upload_image(file):
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    if cloud_name and api_key and api_secret:
        cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
        result = cloudinary.uploader.upload(file, folder='devine_adventures', transformation=[{'quality': 'auto'}])
        return result.get('secure_url')
    return None


@admin_bp.route('/admin')
@login_required
def dashboard():
    admin_required()
    total_users = User.query.count()
    total_tours = Tour.query.count()
    total_bookings = Booking.query.count()
    confirmed_bookings = Booking.query.filter_by(status='confirmed').count()
    pending_bookings = Booking.query.filter(Booking.status.in_(['pending', 'pending_payment'])).count()
    cancelled_bookings = Booking.query.filter_by(status='cancelled').count()
    completed_payments = Payment.query.filter_by(status='completed').all()
    revenue_kes = sum(float(p.amount) for p in completed_payments if p.currency.lower() == 'kes')
    revenue_usd = sum(float(p.amount) for p in completed_payments if p.currency.lower() == 'usd')
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()

    # Bookings over last 6 months
    now = datetime.now(timezone.utc)
    monthly_labels = []
    monthly_bookings = []
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        count = Booking.query.filter(Booking.created_at >= month_start, Booking.created_at < month_end).count()
        rev = sum(
            float(p.amount) for p in completed_payments
            if p.currency.lower() == 'kes' and month_start <= p.created_at.replace(tzinfo=timezone.utc) < month_end
        )
        monthly_labels.append(month_start.strftime('%b %Y'))
        monthly_bookings.append(count)
        monthly_revenue.append(round(rev, 2))

    # Tour performance
    all_tours = Tour.query.all()
    tour_performance = []
    for t in all_tours:
        b_count = t.bookings.count()
        t_rev = sum(
            float(p.amount) for b in t.bookings
            for p in b.payments if p.status == 'completed' and p.currency.lower() == 'kes'
        )
        tour_performance.append({'title': t.title, 'bookings': b_count, 'revenue': t_rev})
    tour_performance.sort(key=lambda x: x['bookings'], reverse=True)

    return render_template('admin/dashboard.html',
        total_users=total_users, total_tours=total_tours,
        total_bookings=total_bookings, confirmed_bookings=confirmed_bookings,
        pending_bookings=pending_bookings, cancelled_bookings=cancelled_bookings,
        revenue_kes=revenue_kes, revenue_usd=revenue_usd,
        recent_bookings=recent_bookings,
        monthly_labels=json.dumps(monthly_labels),
        monthly_bookings=json.dumps(monthly_bookings),
        monthly_revenue=json.dumps(monthly_revenue),
        tour_performance=tour_performance[:8])


@admin_bp.route('/admin/tours')
@login_required
def tours():
    admin_required()
    all_tours = Tour.query.order_by(Tour.created_at.desc()).all()
    return render_template('admin/tours.html', tours=all_tours)


@admin_bp.route('/admin/tours/new', methods=['GET', 'POST'])
@login_required
def new_tour():
    admin_required()
    operators = TourOperator.query.all()
    if request.method == 'POST':
        cover = request.files.get('cover_image')
        cover_url = upload_image(cover) if cover and cover.filename else None
        tour = Tour(
            operator_id=request.form.get('operator_id'),
            title=request.form.get('title'),
            slug=Tour.generate_slug(request.form.get('title')),
            description=request.form.get('description'),
            short_description=request.form.get('short_description'),
            location=request.form.get('location'),
            price_kes=request.form.get('price_kes'),
            price_usd=request.form.get('price_usd'),
            duration_days=request.form.get('duration_days'),
            max_group_size=request.form.get('max_group_size'),
            difficulty=request.form.get('difficulty'),
            category=request.form.get('category'),
            meeting_point=request.form.get('meeting_point'),
            included_items=request.form.get('included_items'),
            excluded_items=request.form.get('excluded_items'),
            deposit_percent=request.form.get('deposit_percent', 100),
            is_featured='is_featured' in request.form,
            is_active='is_active' in request.form,
            cover_image_url=cover_url
        )
        db.session.add(tour)
        db.session.commit()
        flash('Tour created successfully.', 'success')
        return redirect(url_for('admin.tours'))
    return render_template('admin/tour_form.html', tour=None, operators=operators)


@admin_bp.route('/admin/tours/<int:tour_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tour(tour_id):
    admin_required()
    tour = Tour.query.get_or_404(tour_id)
    operators = TourOperator.query.all()
    if request.method == 'POST':
        tour.title = request.form.get('title', tour.title)
        tour.description = request.form.get('description', tour.description)
        tour.short_description = request.form.get('short_description', tour.short_description)
        tour.location = request.form.get('location', tour.location)
        tour.price_kes = request.form.get('price_kes', tour.price_kes)
        tour.price_usd = request.form.get('price_usd', tour.price_usd)
        tour.duration_days = request.form.get('duration_days', tour.duration_days)
        tour.max_group_size = request.form.get('max_group_size', tour.max_group_size)
        tour.difficulty = request.form.get('difficulty', tour.difficulty)
        tour.category = request.form.get('category', tour.category)
        tour.meeting_point = request.form.get('meeting_point', tour.meeting_point)
        tour.included_items = request.form.get('included_items', tour.included_items)
        tour.excluded_items = request.form.get('excluded_items', tour.excluded_items)
        tour.deposit_percent = request.form.get('deposit_percent', tour.deposit_percent)
        tour.is_featured = 'is_featured' in request.form
        tour.is_active = 'is_active' in request.form
        cover = request.files.get('cover_image')
        if cover and cover.filename:
            url = upload_image(cover)
            if url:
                tour.cover_image_url = url
        db.session.commit()
        flash('Tour updated successfully.', 'success')
        return redirect(url_for('admin.tours'))
    return render_template('admin/tour_form.html', tour=tour, operators=operators)


@admin_bp.route('/admin/tours/<int:tour_id>/images', methods=['GET', 'POST'])
@login_required
def tour_images(tour_id):
    admin_required()
    tour = Tour.query.get_or_404(tour_id)
    if request.method == 'POST':
        files = request.files.getlist('images')
        count = 0
        for f in files:
            if f and f.filename:
                url = upload_image(f)
                if url:
                    db.session.add(TourImage(tour_id=tour.id, image_url=url))
                    count += 1
        db.session.commit()
        flash(f'{count} image(s) uploaded.', 'success')
        return redirect(url_for('admin.tour_images', tour_id=tour_id))
    return render_template('admin/tour_images.html', tour=tour)


@admin_bp.route('/admin/tours/images/<int:img_id>/delete', methods=['POST'])
@login_required
def delete_tour_image(img_id):
    admin_required()
    img = TourImage.query.get_or_404(img_id)
    tour_id = img.tour_id
    db.session.delete(img)
    db.session.commit()
    flash('Image deleted.', 'success')
    return redirect(url_for('admin.tour_images', tour_id=tour_id))


@admin_bp.route('/admin/tours/<int:tour_id>/delete', methods=['POST'])
@login_required
def delete_tour(tour_id):
    admin_required()
    tour = Tour.query.get_or_404(tour_id)
    db.session.delete(tour)
    db.session.commit()
    flash('Tour deleted.', 'success')
    return redirect(url_for('admin.tours'))


@admin_bp.route('/admin/users')
@login_required
def users():
    admin_required()
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    admin_required()
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
def change_role(user_id):
    admin_required()
    user = User.query.get_or_404(user_id)
    role = request.form.get('role')
    if role in ('traveler', 'operator', 'admin'):
        user.role = role
        db.session.commit()
        flash(f'Role updated to {role}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/admin/bookings')
@login_required
def bookings():
    admin_required()
    all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=all_bookings)


@admin_bp.route('/admin/bookings/<int:booking_id>/status', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    admin_required()
    booking = Booking.query.get_or_404(booking_id)
    status = request.form.get('status')
    if status in ('pending', 'confirmed', 'cancelled', 'completed'):
        booking.status = status
        db.session.commit()
        flash('Booking status updated.', 'success')
    return redirect(url_for('admin.bookings'))


@admin_bp.route('/admin/reviews')
@login_required
def reviews():
    admin_required()
    from app.models.booking import Review
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', all_reviews=all_reviews)


@admin_bp.route('/admin/revenue')
@login_required
def revenue():
    admin_required()
    completed_payments = Payment.query.filter_by(status='completed').order_by(Payment.created_at.desc()).all()
    stripe_total = sum(float(p.amount) for p in completed_payments if p.method == 'stripe')
    mpesa_total = sum(float(p.amount) for p in completed_payments if p.method == 'mpesa')
    unified_kes = mpesa_total + (stripe_total * EXCHANGE_RATE)
    unified_usd = stripe_total + (mpesa_total / EXCHANGE_RATE)
    return render_template('admin/revenue.html',
        payments=completed_payments,
        stripe_total=stripe_total, mpesa_total=mpesa_total,
        unified_kes=unified_kes, unified_usd=unified_usd,
        exchange_rate=EXCHANGE_RATE)
