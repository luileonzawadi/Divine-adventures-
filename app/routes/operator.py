import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, abort, Response
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Tour, TourDate, Booking, TourOperator

operator_bp = Blueprint('operator', __name__)


def get_operator_profile_or_403():
    """
    Validates that the current user has an operator/admin profile.
    """
    if not current_user.is_authenticated:
        abort(401)
    
    if current_user.role == 'admin':
        # Admin can view any operator dashboard, default to first operator
        profile = TourOperator.query.first()
        if not profile:
            abort(404, description="No tour operator accounts found in the database.")
        return profile

    if current_user.role != 'operator':
        abort(403, description="Access restricted to Tour Operators only.")

    profile = current_user.operator_profile
    if not profile:
        abort(403, description="Your Tour Operator profile is not configured.")
        
    return profile


@operator_bp.route('/operator/dashboard')
@login_required
def dashboard():
    """
    Lists operator's tours, departure dates, and booking summaries.
    """
    profile = get_operator_profile_or_403()
    tours = profile.tours.all()
    
    # Calculate simple stats
    revenue_kes = 0
    revenue_usd = 0
    total_confirmed_bookings = 0

    for tour in tours:
        for booking in tour.bookings.filter_by(status='confirmed').all():
            revenue_kes += booking.total_price_kes
            revenue_usd += booking.total_price_usd
            total_confirmed_bookings += 1

    return render_template(
        'operator/dashboard.html',
        profile=profile,
        tours=tours,
        revenue_kes=revenue_kes,
        revenue_usd=revenue_usd,
        total_bookings=total_confirmed_bookings
    )


@operator_bp.route('/operator/dates/<int:date_id>/bookings')
@login_required
def manifest(date_id):
    """
    Displays traveler list for a specific tour date.
    """
    profile = get_operator_profile_or_403()
    tour_date = TourDate.query.get_or_404(date_id)

    # Security check: Make sure this tour belongs to the operator
    if current_user.role != 'admin' and tour_date.tour.operator_id != profile.id:
        abort(403)

    bookings = tour_date.bookings.order_by(Booking.created_at.desc()).all()
    return render_template('operator/manifest.html', tour_date=tour_date, bookings=bookings)


@operator_bp.route('/operator/bookings/<int:booking_id>/check-in', methods=['POST'])
@login_required
def check_in(booking_id):
    """
    Toggles the is_checked_in status of a passenger.
    """
    profile = get_operator_profile_or_403()
    booking = Booking.query.get_or_404(booking_id)

    # Security check
    if current_user.role != 'admin' and booking.tour.operator_id != profile.id:
        abort(403)

    # Toggle status
    booking.is_checked_in = not booking.is_checked_in
    if booking.is_checked_in:
        booking.checked_in_at = datetime.now(timezone.utc)
    else:
        booking.checked_in_at = None

    db.session.commit()
    
    status_msg = "Checked In" if booking.is_checked_in else "Check-in Undone"
    flash(f"Status updated: {booking.traveler_name} is now marked as {status_msg}.", "success")
    
    return redirect(url_for('operator.manifest', date_id=booking.tour_date_id))


@operator_bp.route('/operator/dates/<int:date_id>/bookings/csv')
@login_required
def download_csv(date_id):
    """
    Generates a downloadable CSV containing the participant list for a tour date.
    """
    profile = get_operator_profile_or_403()
    tour_date = TourDate.query.get_or_404(date_id)

    # Security check
    if current_user.role != 'admin' and tour_date.tour.operator_id != profile.id:
        abort(403)

    bookings = tour_date.bookings.filter(Booking.status != 'cancelled').all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        'Booking Reference',
        'Traveler Name',
        'Traveler Email',
        'Traveler Phone',
        'Nationality',
        'Emergency Contact Name',
        'Emergency Contact Phone',
        'Guests Count',
        'Total Price (KES)',
        'Total Price (USD)',
        'Checked In',
        'Checked In At'
    ])

    for b in bookings:
        writer.writerow([
            b.booking_reference,
            b.traveler_name,
            b.traveler_email,
            b.traveler_phone,
            b.traveler_nationality,
            b.emergency_contact_name,
            b.emergency_contact_phone,
            b.num_guests,
            float(b.total_price_kes),
            float(b.total_price_usd),
            'Yes' if b.is_checked_in else 'No',
            b.checked_in_at.strftime('%Y-%m-%d %H:%M:%S') if b.checked_in_at else 'N/A'
        ])

    csv_data = output.getvalue()
    output.close()

    filename = f"manifest_{tour_date.tour.slug}_{tour_date.start_date.strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
