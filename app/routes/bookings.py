from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Tour, TourDate, Booking, Waitlist
from app.utils.emails import send_booking_confirmation, send_waitlist_notification

bookings_bp = Blueprint('bookings', __name__)


@bookings_bp.route('/tours/<slug>/book', methods=['GET', 'POST'])
@login_required
def book_tour(slug):
    """
    Handles the 4-step wizard booking flow.
    Saves state in Flask session.
    """
    tour = Tour.query.filter_by(slug=slug, is_active=True).first_or_404()
    step = request.args.get('step', '1')

    # Initialize session key if not exists
    if 'booking_flow' not in session:
        session['booking_flow'] = {}

    flow_data = session['booking_flow']

    # Step 1: Select Tour Date and Participant Count
    if step == '1':
        if request.method == 'POST':
            date_id = request.form.get('tour_date_id', type=int)
            num_guests = request.form.get('num_guests', type=int)

            if not date_id or not num_guests or num_guests < 1:
                flash("Please select a valid date and participant count.", "warning")
                return redirect(url_for('bookings.book_tour', slug=slug, step='1'))

            tour_date = TourDate.query.get_or_404(date_id)

            # Availability validation check
            if tour_date.spots_available < num_guests:
                flash(f"Only {tour_date.spots_available} spots are left on this date. Choose another date or join the waitlist.", "danger")
                return redirect(url_for('bookings.book_tour', slug=slug, step='1'))

            # Save step 1 data
            flow_data['tour_date_id'] = date_id
            flow_data['num_guests'] = num_guests
            session.modified = True
            
            return redirect(url_for('bookings.book_tour', slug=slug, step='2'))

        # GET request for Step 1
        active_dates = tour.dates.filter_by(is_active=True).all()
        return render_template('booking/book_step1.html', tour=tour, active_dates=active_dates)

    # Step 2: Traveler Personal & Emergency Details
    elif step == '2':
        if 'tour_date_id' not in flow_data:
            return redirect(url_for('bookings.book_tour', slug=slug, step='1'))

        if request.method == 'POST':
            name = request.form.get('traveler_name')
            email = request.form.get('traveler_email')
            phone = request.form.get('traveler_phone')
            nationality = request.form.get('traveler_nationality')
            emergency_name = request.form.get('emergency_contact_name')
            emergency_phone = request.form.get('emergency_contact_phone')
            special_requests = request.form.get('special_requests', '')

            # Basic validations
            if not all([name, email, phone, nationality, emergency_name, emergency_phone]):
                flash("All traveler details and emergency contact fields are required.", "warning")
                return redirect(url_for('bookings.book_tour', slug=slug, step='2'))

            # Save step 2 data
            flow_data['traveler_name'] = name
            flow_data['traveler_email'] = email
            flow_data['traveler_phone'] = phone
            flow_data['traveler_nationality'] = nationality
            flow_data['emergency_contact_name'] = emergency_name
            flow_data['emergency_contact_phone'] = emergency_phone
            flow_data['special_requests'] = special_requests
            session.modified = True

            return redirect(url_for('bookings.book_tour', slug=slug, step='3'))

        # Prefill form fields from user profile if empty
        prefill = {
            'name': flow_data.get('traveler_name') or current_user.full_name,
            'email': flow_data.get('traveler_email') or current_user.email,
            'phone': flow_data.get('traveler_phone') or current_user.phone or '',
            'nationality': flow_data.get('traveler_nationality') or '',
            'emergency_name': flow_data.get('emergency_contact_name') or '',
            'emergency_phone': flow_data.get('emergency_contact_phone') or '',
            'special_requests': flow_data.get('special_requests') or ''
        }
        return render_template('booking/book_step2.html', tour=tour, prefill=prefill)

    # Step 3: Summary and Pricing
    elif step == '3':
        if 'tour_date_id' not in flow_data or 'traveler_name' not in flow_data:
            return redirect(url_for('bookings.book_tour', slug=slug, step='1'))

        tour_date = TourDate.query.get_or_404(flow_data['tour_date_id'])
        
        # Calculate dynamic prices
        price_kes = tour_date.effective_price_kes * flow_data['num_guests']
        price_usd = tour_date.effective_price_usd * flow_data['num_guests']

        deposit_percent = tour.deposit_percent if tour.deposit_percent is not None else 100
        deposit_kes = (price_kes * deposit_percent) / 100
        deposit_usd = (price_usd * deposit_percent) / 100
        balance_kes = price_kes - deposit_kes
        balance_usd = price_usd - deposit_usd

        if request.method == 'POST':
            # Save step 3 price totals
            flow_data['total_price_kes'] = float(price_kes)
            flow_data['total_price_usd'] = float(price_usd)
            session.modified = True
            
            return redirect(url_for('bookings.book_tour', slug=slug, step='4'))

        return render_template(
            'booking/book_step3.html',
            tour=tour,
            tour_date=tour_date,
            flow_data=flow_data,
            price_kes=price_kes,
            price_usd=price_usd,
            deposit_percent=deposit_percent,
            deposit_kes=deposit_kes,
            deposit_usd=deposit_usd,
            balance_kes=balance_kes,
            balance_usd=balance_usd
        )

    # Step 4: Confirm Booking & Proceed to Payment Selection
    elif step == '4':
        if 'total_price_kes' not in flow_data:
            return redirect(url_for('bookings.book_tour', slug=slug, step='1'))

        tour_date = TourDate.query.get_or_404(flow_data['tour_date_id'])

        deposit_percent = tour.deposit_percent if tour.deposit_percent is not None else 100
        price_kes = float(flow_data['total_price_kes'])
        price_usd = float(flow_data['total_price_usd'])
        deposit_kes = (price_kes * deposit_percent) / 100
        deposit_usd = (price_usd * deposit_percent) / 100
        balance_kes = price_kes - deposit_kes
        balance_usd = price_usd - deposit_usd

        if request.method == 'POST':
            # Double check seats lock to avoid double booking
            if tour_date.spots_available < flow_data['num_guests']:
                flash("The spots are no longer available for this date. Booking cancelled.", "danger")
                session.pop('booking_flow', None)
                return redirect(url_for('bookings.book_tour', slug=slug, step='1'))

            # Create pending_payment Booking record
            booking = Booking(
                user_id=current_user.id,
                tour_id=tour.id,
                tour_date_id=tour_date.id,
                num_guests=flow_data['num_guests'],
                total_price_kes=price_kes,
                total_price_usd=price_usd,
                deposit_paid_kes=0.00,
                deposit_paid_usd=0.00,
                status='pending_payment',
                traveler_name=flow_data['traveler_name'],
                traveler_email=flow_data['traveler_email'],
                traveler_phone=flow_data['traveler_phone'],
                traveler_nationality=flow_data['traveler_nationality'],
                emergency_contact_name=flow_data['emergency_contact_name'],
                emergency_contact_phone=flow_data['emergency_contact_phone'],
                special_requests=flow_data['special_requests'],
                booking_reference=Booking.generate_reference()
            )

            # Increment count of current bookings on this departure date
            tour_date.current_bookings += flow_data['num_guests']
            
            db.session.add(booking)
            db.session.commit()

            # Clean session values
            ref = booking.booking_reference
            session.pop('booking_flow', None)

            flash("Booking reserved! Please choose a payment method to confirm.", "info")
            return redirect(url_for('payments.pay_booking', booking_ref=ref))

        return render_template(
            'booking/book_step4.html',
            tour=tour,
            flow_data=flow_data,
            deposit_percent=deposit_percent,
            deposit_kes=deposit_kes,
            deposit_usd=deposit_usd,
            balance_kes=balance_kes,
            balance_usd=balance_usd
        )

    abort(404)


@bookings_bp.route('/bookings/success/<booking_ref>')
@login_required
def booking_success(booking_ref):
    """
    Renders receipt details upon successful booking confirmation.
    """
    booking = Booking.query.filter_by(booking_reference=booking_ref, user_id=current_user.id).first_or_404()
    return render_template('booking/success.html', booking=booking)


@bookings_bp.route('/tours/dates/<int:date_id>/waitlist', methods=['POST'])
@login_required
def join_waitlist(date_id):
    """
    Registers a traveler on the waitlist for a sold-out date.
    """
    tour_date = TourDate.query.get_or_404(date_id)
    
    if not tour_date.is_sold_out:
        flash("Spots are still available for this date. Go ahead and book directly!", "warning")
        return redirect(url_for('main.index'))

    name = request.form.get('waitlist_name')
    email = request.form.get('waitlist_email')
    phone = request.form.get('waitlist_phone', '')

    if not name or not email:
        flash("Name and email are required to join the waitlist.", "warning")
        return redirect(url_for('main.index'))

    # Check duplicate waitlist entry
    exists = Waitlist.query.filter_by(tour_date_id=date_id, email=email, is_notified=False).first()
    if exists:
        flash("You are already on the waitlist for this departure date.", "info")
        return redirect(url_for('main.index'))

    entry = Waitlist(
        tour_date_id=date_id,
        user_id=current_user.id,
        name=name,
        email=email,
        phone=phone
    )
    db.session.add(entry)
    db.session.commit()

    flash("You have successfully joined the waitlist. We will notify you if a spot opens up!", "success")
    return redirect(url_for('main.index'))


@bookings_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Traveler dashboard to view and manage active bookings.
    """
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    waitlist = Waitlist.query.filter_by(user_id=current_user.id).order_by(Waitlist.created_at.desc()).all()
    return render_template('booking/dashboard.html', bookings=bookings, waitlist=waitlist)


@bookings_bp.route('/bookings/<booking_ref>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_ref):
    """
    Cancels traveler booking and handles waitlist auto-notifications.
    """
    booking = Booking.query.filter_by(booking_reference=booking_ref, user_id=current_user.id).first_or_404()

    if not booking.is_cancellable:
        flash("This booking cannot be cancelled.", "warning")
        return redirect(url_for('bookings.dashboard'))

    tour_date = booking.tour_date

    # Update states
    booking.status = 'cancelled'
    
    # Restore capacity on the tour date
    if tour_date:
        tour_date.current_bookings = max(0, tour_date.current_bookings - booking.num_guests)

        # Waitlist trigger notification:
        # Search for earliest waitlist registrant who hasn't been notified yet
        earliest_waitlist = Waitlist.query.filter_by(
            tour_date_id=tour_date.id,
            is_notified=False
        ).order_by(Waitlist.created_at.asc()).first()

        if earliest_waitlist:
            # Send notification email invite
            send_waitlist_notification(earliest_waitlist)
            
            # Update entry state to avoid multiple emails
            earliest_waitlist.is_notified = True
            earliest_waitlist.notified_at = datetime.now(timezone.utc)
            db.session.add(earliest_waitlist)

    db.session.commit()
    flash("Your booking has been cancelled successfully. Refund (if applicable) will be processed.", "success")
    return redirect(url_for('bookings.dashboard'))
