import os
import uuid
import time
import stripe
import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models import Booking, Payment, TourDate, Waitlist
from app.utils.mpesa import MpesaConnector
from app.utils.emails import send_booking_confirmation, send_waitlist_notification

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


def is_stripe_configured():
    return bool(stripe.api_key)


def check_waitlist_slots(tour_date):
    """
    Checks if there is available capacity on the departure date and
    notifies the earliest waitlisted traveler.
    """
    if not tour_date:
        return
    
    if tour_date.spots_available > 0:
        earliest_waitlist = Waitlist.query.filter_by(
            tour_date_id=tour_date.id,
            is_notified=False
        ).order_by(Waitlist.created_at.asc()).first()

        if earliest_waitlist:
            try:
                send_waitlist_notification(earliest_waitlist)
                earliest_waitlist.is_notified = True
                earliest_waitlist.notified_at = datetime.now(timezone.utc)
                db.session.add(earliest_waitlist)
                db.session.commit()
                logger.info(f"Waitlist notification sent to {earliest_waitlist.email} for date {tour_date.id}")
            except Exception as e:
                logger.error(f"Failed to send waitlist email: {str(e)}")


@payments_bp.route('/bookings/<booking_ref>/pay', methods=['GET', 'POST'])
@login_required
def pay_booking(booking_ref):
    """
    Renders payment selector (GET) or initiates payment transaction (POST).
    """
    booking = Booking.query.filter_by(booking_reference=booking_ref, user_id=current_user.id).first_or_404()

    if booking.status == 'confirmed':
        flash("This booking is already paid and confirmed.", "info")
        return redirect(url_for('bookings.booking_success', booking_ref=booking_ref))

    if request.method == 'POST':
        method = request.form.get('payment_method')

        if method == 'mpesa':
            phone = request.form.get('phone_number')
            if not phone:
                flash("M-Pesa payment requires a valid phone number.", "warning")
                return redirect(url_for('payments.pay_booking', booking_ref=booking_ref))

            # Calculate deposit amount in KES
            amount_kes = booking.deposit_amount_kes

            # Trigger STK push
            mpesa = MpesaConnector()
            response = mpesa.initiate_stk_push(phone, amount_kes, booking.booking_reference)

            if response.get("ResponseCode") == "0":
                # Create a pending Payment record
                checkout_id = response.get("CheckoutRequestID")
                payment = Payment(
                    booking_id=booking.id,
                    amount=amount_kes,
                    currency='kes',
                    method='mpesa',
                    status='pending',
                    reference=checkout_id
                )
                db.session.add(payment)
                db.session.commit()

                return redirect(url_for('payments.poll_payment', booking_ref=booking_ref))
            else:
                flash(f"Failed to initiate M-Pesa STK Push: {response.get('ResponseDescription', 'Unknown error')}", "danger")
                return redirect(url_for('payments.pay_booking', booking_ref=booking_ref))

        elif method == 'stripe':
            # Calculate deposit amount in USD
            amount_usd = booking.deposit_amount_usd

            if is_stripe_configured():
                try:
                    # Build real Stripe checkout session
                    session = stripe.checkout.Session.create(
                        payment_method_types=['card'],
                        line_items=[{
                            'price_data': {
                                'currency': 'usd',
                                'product_data': {
                                    'name': f"Tour Deposit: {booking.tour.title}",
                                    'description': f"Booking Reference: {booking.booking_reference}",
                                },
                                'unit_amount': int(round(amount_usd * 100)),  # in cents
                            },
                            'quantity': 1,
                        }],
                        mode='payment',
                        success_url=request.host_url.rstrip('/') + url_for('payments.stripe_success') + '?session_id={CHECKOUT_SESSION_ID}',
                        cancel_url=request.host_url.rstrip('/') + url_for('payments.pay_booking', booking_ref=booking_ref),
                        metadata={
                            'booking_reference': booking.booking_reference
                        }
                    )

                    # Create a pending Payment record
                    payment = Payment(
                        booking_id=booking.id,
                        amount=amount_usd,
                        currency='usd',
                        method='stripe',
                        status='pending',
                        reference=session.id
                    )
                    db.session.add(payment)
                    db.session.commit()

                    return redirect(session.url, code=303)
                except Exception as e:
                    logger.error(f"Stripe session creation error: {str(e)}")
                    flash(f"Stripe checkout failed: {str(e)}", "danger")
                    return redirect(url_for('payments.pay_booking', booking_ref=booking_ref))
            else:
                # Simulation Mode (Redirect to mock stripe screen)
                mock_session_id = f"mock_stripe_session_{uuid.uuid4().hex[:8]}"
                payment = Payment(
                    booking_id=booking.id,
                    amount=amount_usd,
                    currency='usd',
                    method='stripe',
                    status='pending',
                    reference=mock_session_id
                )
                db.session.add(payment)
                db.session.commit()

                return redirect(url_for('payments.mock_stripe_checkout', booking_ref=booking_ref))

        else:
            flash("Invalid payment method selected.", "warning")
            return redirect(url_for('payments.pay_booking', booking_ref=booking_ref))

    return render_template('booking/payment_method.html', booking=booking)


@payments_bp.route('/payments/stripe/mock_checkout/<booking_ref>', methods=['GET', 'POST'])
@login_required
def mock_stripe_checkout(booking_ref):
    """
    Renders mock Stripe payment gateway screen for testing checkout flows.
    """
    booking = Booking.query.filter_by(booking_reference=booking_ref, user_id=current_user.id).first_or_404()
    payment = Payment.query.filter_by(booking_id=booking.id, method='stripe', status='pending').order_by(Payment.created_at.desc()).first_or_404()

    if request.method == 'POST':
        # Trigger webhook simulation via POST to /payments/stripe/webhook
        # Since it's local development, we can trigger the DB update directly
        # or simulate the JSON structure post. We will trigger the DB update
        # directly in the handler so it's clean, but print/log the webhook format.
        logger.info(f"[STRIPE SIMULATION] User confirmed mock payment for session {payment.reference}")
        
        # Simulate webhook processing
        return render_template('booking/stripe_mock_success_submit.html', booking=booking, payment=payment)

    return render_template('booking/mock_stripe_checkout.html', booking=booking, payment=payment)


@payments_bp.route('/payments/stripe/success')
@login_required
def stripe_success():
    """
    Stripe Checkout Session redirect landing page.
    """
    session_id = request.args.get('session_id')
    return render_template('booking/stripe_success.html', session_id=session_id)


@payments_bp.route('/payments/stripe/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    """
    Handles checkout.session.completed webhook from Stripe.
    """
    payload = request.data
    sig_header = request.headers.get('STRIPE_SIGNATURE')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    event = None

    if not endpoint_secret:
        # Development / Simulation mode: parse JSON event directly
        try:
            event = request.json
            logger.info("[STRIPE WEBHOOK SIMULATION] Bypassing signature verification.")
        except Exception as e:
            logger.error(f"Failed to parse JSON in webhook simulation: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 400
    else:
        # Production mode: verify signature
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid Stripe Webhook signature: {str(e)}")
            return jsonify({"status": "error", "message": "Invalid signature"}), 400
        except Exception as e:
            logger.error(f"Stripe Webhook error: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 400

    # Handle event type
    event_type = event.get('type')
    if event_type == 'checkout.session.completed':
        session = event.get('data', {}).get('object', {})
        booking_ref = session.get('metadata', {}).get('booking_reference')
        session_id = session.get('id')

        # Retrieve booking by reference or payment session reference
        booking = None
        payment = None

        if booking_ref:
            booking = Booking.query.filter_by(booking_reference=booking_ref).first()
        
        if session_id:
            payment = Payment.query.filter_by(reference=session_id).first()
            if not booking and payment:
                booking = Booking.query.get(payment.booking_id)

        if not booking:
            logger.error(f"Stripe webhook: booking not found (Ref: {booking_ref}, Session: {session_id})")
            return jsonify({"status": "error", "message": "Booking not found"}), 404

        if not payment and booking:
            payment = Payment.query.filter_by(booking_id=booking.id, method='stripe', status='pending').first()

        if payment and payment.status == 'pending':
            # Complete Payment
            payment.status = 'completed'
            payment.reference = session_id or payment.reference
            
            # Update Booking
            booking.deposit_paid_usd = payment.amount
            booking.status = 'confirmed'
            
            db.session.commit()

            # Dispatch confirmation email
            try:
                send_booking_confirmation(booking)
            except Exception as e:
                logger.error(f"Failed to send booking email: {str(e)}")

            # Trigger waitlist slots check
            check_waitlist_slots(booking.tour_date)
            
            logger.info(f"Stripe payment success for Booking {booking.booking_reference}. Confirmed!")
        else:
            logger.warning(f"Payment already processed or missing for booking {booking.booking_reference}")

    return jsonify({"status": "success"}), 200


@payments_bp.route('/payments/mpesa/callback', methods=['POST'])
@csrf.exempt
def mpesa_callback():
    """
    Handles M-Pesa validation STK callback payload from Safaricom.
    """
    # Safaricom allows custom parameters in URL: /payments/mpesa/callback?booking_ref=DA-XXXX-XXXX
    booking_ref = request.args.get('booking_ref')
    data = request.json

    if not data or 'Body' not in data or 'stkCallback' not in data['Body']:
        logger.error("Invalid M-Pesa callback payload format received.")
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid payload format"}), 400

    callback_data = data['Body']['stkCallback']
    result_code = callback_data.get('ResultCode')
    result_desc = callback_data.get('ResultDesc')
    checkout_request_id = callback_data.get('CheckoutRequestID')

    # Find booking and payment
    booking = None
    payment = None

    if checkout_request_id:
        payment = Payment.query.filter_by(reference=checkout_request_id).first()
        if payment:
            booking = Booking.query.get(payment.booking_id)

    if not booking and booking_ref:
        booking = Booking.query.filter_by(booking_reference=booking_ref).first()
        if booking and not payment:
            payment = Payment.query.filter_by(booking_id=booking.id, method='mpesa', status='pending').first()

    if not booking or not payment:
        logger.error(f"M-Pesa callback: booking/payment not found (Ref: {booking_ref}, CheckoutID: {checkout_request_id})")
        return jsonify({"ResultCode": 1, "ResultDesc": "Booking or Payment not found"}), 404

    # Process Result
    if result_code == 0:
        # Extract Receipt
        receipt_number = None
        metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
        for item in metadata:
            if item.get('Name') == 'MpesaReceiptNumber':
                receipt_number = item.get('Value')
                break

        # Complete Payment record
        payment.status = 'completed'
        if receipt_number:
            payment.reference = receipt_number

        # Update Booking state
        booking.deposit_paid_kes = payment.amount
        booking.status = 'confirmed'
        
        db.session.commit()

        # Send confirmation email
        try:
            send_booking_confirmation(booking)
        except Exception as e:
            logger.error(f"Failed to send booking email: {str(e)}")

        # Trigger waitlist slots check
        check_waitlist_slots(booking.tour_date)

        logger.info(f"M-Pesa callback success for Booking {booking.booking_reference}. Confirmed!")
    else:
        # Mark payment as failed
        payment.status = 'failed'
        payment.reference = f"failed_{checkout_request_id}"
        
        # Release capacity back to the tour date since payment failed
        if booking.status == 'pending_payment':
            booking.status = 'cancelled'  # release slots
            if booking.tour_date:
                booking.tour_date.current_bookings = max(0, booking.tour_date.current_bookings - booking.num_guests)
                
        db.session.commit()
        
        # Trigger waitlist slots check because slots opened up
        check_waitlist_slots(booking.tour_date)
        
        logger.warning(f"M-Pesa payment failed for Booking {booking.booking_reference}: {result_desc} (Code: {result_code})")

    return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200


@payments_bp.route('/payments/status/<booking_ref>', methods=['GET'])
def get_payment_status(booking_ref):
    """
    Returns payment status JSON used by frontend polling scripts.
    """
    booking = Booking.query.filter_by(booking_reference=booking_ref).first_or_404()
    
    # Get latest payment record
    payment = Payment.query.filter_by(booking_id=booking.id).order_by(Payment.created_at.desc()).first()
    payment_status = payment.status if payment else 'unknown'

    return jsonify({
        "status": booking.status,
        "payment_status": payment_status,
        "booking_reference": booking.booking_reference
    })


@payments_bp.route('/payments/poll/<booking_ref>', methods=['GET'])
@login_required
def poll_payment(booking_ref):
    """
    Renders loading/polling screen for payment validation.
    """
    booking = Booking.query.filter_by(booking_reference=booking_ref, user_id=current_user.id).first_or_404()
    
    # Fetch pending payment
    payment = Payment.query.filter_by(booking_id=booking.id, status='pending').order_by(Payment.created_at.desc()).first()
    
    # If no pending payment but booking is confirmed, direct to success
    if booking.status == 'confirmed':
        return redirect(url_for('bookings.booking_success', booking_ref=booking_ref))

    checkout_request_id = payment.reference if payment else 'unknown'

    return render_template(
        'booking/poll.html',
        booking=booking,
        payment=payment,
        checkout_request_id=checkout_request_id
    )
