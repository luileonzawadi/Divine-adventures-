import os
import uuid
import logging
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort, jsonify
)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Tour, Booking, Review, ReviewPhoto, TourDate

logger = logging.getLogger(__name__)
reviews_bp = Blueprint('reviews', __name__)

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads', 'reviews')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_PHOTOS = 3


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_photo(file):
    """Upload photo to Cloudinary if configured, else save locally."""
    try:
        import cloudinary
        import cloudinary.uploader
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')

        if cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name, api_key=api_key, api_secret=api_secret
            )
            result = cloudinary.uploader.upload(
                file, folder='devine_adventures/reviews',
                transformation=[{'width': 1200, 'height': 900, 'crop': 'limit', 'quality': 'auto'}]
            )
            return result.get('secure_url')
    except Exception as e:
        logger.warning(f"Cloudinary upload failed, falling back to local: {e}")

    # Local fallback
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return f"/static/uploads/reviews/{filename}"


# ─────────────────────────────────────────
# REVIEW SUBMISSION
# ─────────────────────────────────────────

@reviews_bp.route('/tours/<slug>/review', methods=['GET', 'POST'])
@login_required
def submit_review(slug):
    """Verified-traveler review submission form."""
    tour = Tour.query.filter_by(slug=slug, is_active=True).first_or_404()
    booking_ref = request.args.get('booking_ref') or request.form.get('booking_ref')

    # Verify the traveler has a completed booking for this tour
    booking = None
    if booking_ref:
        booking = Booking.query.filter_by(
            booking_reference=booking_ref,
            user_id=current_user.id,
            tour_id=tour.id,
            status='completed'
        ).first()

    if not booking:
        # Check any completed booking for this user + tour
        booking = Booking.query.filter_by(
            user_id=current_user.id,
            tour_id=tour.id,
            status='completed'
        ).first()

    if not booking:
        flash(
            "Only travelers who have completed this tour can leave a review. "
            "Your booking must be marked 'completed' first.",
            "warning"
        )
        return redirect(url_for('bookings.dashboard'))

    # Already reviewed?
    existing = Review.query.filter_by(
        user_id=current_user.id, tour_id=tour.id
    ).first()
    if existing:
        flash("You have already submitted a review for this tour. Thank you!", "info")
        return redirect(url_for('main.tour_detail', slug=slug))

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        title = request.form.get('title', '').strip()
        comment = request.form.get('comment', '').strip()
        photos = request.files.getlist('photos')

        # Validation
        errors = []
        if not rating or not (1 <= rating <= 5):
            errors.append("Please select a star rating (1–5).")
        if not comment or len(comment) < 20:
            errors.append("Your review must be at least 20 characters.")
        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template('booking/review_submit.html', tour=tour, booking=booking)

        # Create review
        review = Review(
            user_id=current_user.id,
            tour_id=tour.id,
            booking_id=booking.id,
            rating=rating,
            title=title or None,
            comment=comment,
            is_approved=True,
            is_flagged=False,
        )
        db.session.add(review)
        db.session.flush()  # get review.id

        # Save up to MAX_PHOTOS photos
        saved = 0
        for photo in photos:
            if saved >= MAX_PHOTOS:
                break
            if photo and photo.filename and allowed_file(photo.filename):
                try:
                    url = save_photo(photo)
                    rp = ReviewPhoto(review_id=review.id, image_url=url)
                    db.session.add(rp)
                    saved += 1
                except Exception as e:
                    logger.error(f"Photo upload error: {e}")

        db.session.commit()
        flash("Thank you! Your review has been published. 🌟", "success")
        return redirect(url_for('main.tour_detail', slug=slug))

    return render_template('booking/review_submit.html', tour=tour, booking=booking)


# ─────────────────────────────────────────
# OPERATOR REPLY
# ─────────────────────────────────────────

@reviews_bp.route('/operator/reviews/<int:review_id>/reply', methods=['POST'])
@login_required
def operator_reply(review_id):
    """Operator posts a public reply to a traveler review."""
    from app.models import TourOperator
    review = Review.query.get_or_404(review_id)

    # Permission: operator must own the tour, or be admin
    if current_user.role == 'admin':
        pass
    elif current_user.role == 'operator':
        profile = current_user.operator_profile
        if not profile or review.tour.operator_id != profile.id:
            abort(403)
    else:
        abort(403)

    response_text = request.form.get('operator_response', '').strip()
    if not response_text:
        flash("Reply cannot be empty.", "warning")
        return redirect(request.referrer or url_for('main.tour_detail', slug=review.tour.slug))

    review.operator_response = response_text
    review.operator_responded_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Your reply has been posted publicly.", "success")
    return redirect(url_for('main.tour_detail', slug=review.tour.slug) + '#reviews')


# ─────────────────────────────────────────
# ADMIN MODERATION
# ─────────────────────────────────────────

@reviews_bp.route('/admin/reviews')
@login_required
def admin_reviews():
    """Admin moderation board for all reviews."""
    if current_user.role != 'admin':
        abort(403)

    flagged = Review.query.filter_by(is_flagged=True).order_by(Review.created_at.desc()).all()
    all_reviews = Review.query.order_by(Review.created_at.desc()).limit(100).all()
    return render_template('admin/reviews.html', flagged=flagged, all_reviews=all_reviews)


@reviews_bp.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
@login_required
def admin_approve_review(review_id):
    """Toggle a review's approval state."""
    if current_user.role != 'admin':
        abort(403)
    review = Review.query.get_or_404(review_id)
    review.is_approved = not review.is_approved
    review.is_flagged = False
    db.session.commit()
    state = "approved" if review.is_approved else "hidden"
    flash(f"Review by {review.user.full_name} is now {state}.", "success")
    return redirect(url_for('reviews.admin_reviews'))


@reviews_bp.route('/admin/reviews/<int:review_id>/flag', methods=['POST'])
@login_required
def admin_flag_review(review_id):
    """Flag a review as inappropriate."""
    if current_user.role != 'admin':
        abort(403)
    review = Review.query.get_or_404(review_id)
    review.is_flagged = True
    review.is_approved = False
    db.session.commit()
    flash(f"Review flagged and hidden from public view.", "warning")
    return redirect(url_for('reviews.admin_reviews'))


@reviews_bp.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def admin_delete_review(review_id):
    """Permanently delete a review."""
    if current_user.role != 'admin':
        abort(403)
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review permanently deleted.", "success")
    return redirect(url_for('reviews.admin_reviews'))
