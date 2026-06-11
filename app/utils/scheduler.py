"""
APScheduler job: scans for confirmed bookings whose tour date has passed,
transitions them to 'completed', and sends review request emails.
"""
import logging
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)


def send_review_request_email(booking):
    """Send a review invitation email to the traveler."""
    from app.utils.emails import send_email
    review_url = f"http://localhost:5000/tours/{booking.tour.slug}/review?booking_ref={booking.booking_reference}"
    subject = f"How was your adventure? Share your {booking.tour.title} review"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #111827; max-width: 600px; margin: 0 auto; border: 1px solid #E9ECEF; border-radius: 8px; overflow: hidden;">
      <div style="background: linear-gradient(135deg, #1B4332, #2D6A4F); padding: 32px; text-align: center; color: white;">
        <div style="font-size: 2rem; margin-bottom: 8px;">⭐</div>
        <h1 style="margin: 0; font-size: 22px;">Your Adventure Is Complete!</h1>
        <p style="margin: 8px 0 0; font-size: 15px; opacity: 0.9;">We'd love to hear how it went</p>
      </div>
      <div style="padding: 32px;">
        <p>Dear {booking.traveler_name},</p>
        <p>We hope you had an incredible time on <strong>{booking.tour.title}</strong>! Your experience and insights help future adventurers discover great tours.</p>
        <p>Take 2 minutes to rate your experience and upload your favourite trip photos — your review will be featured on the tour page with a <strong>Verified Traveler</strong> badge.</p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{review_url}" style="background: linear-gradient(135deg, #E85D04, #C44D03); color: white; text-decoration: none; padding: 14px 32px; font-weight: bold; border-radius: 8px; display: inline-block; font-size: 16px; box-shadow: 0 4px 15px rgba(232, 93, 4, 0.4);">
            ⭐ Write My Review
          </a>
        </div>
        <div style="background-color: #F8F9FA; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
          <h4 style="color: #1B4332; margin-top: 0; margin-bottom: 8px;">📸 You can upload up to 3 trip photos</h4>
          <p style="margin: 0; font-size: 14px; color: #6B7280;">Your photos may be featured on the tour gallery and homepage.</p>
        </div>
        <p style="font-size: 13px; color: #6B7280;">Reference: {booking.booking_reference}</p>
        <p>Thank you for adventuring with us!<br><strong>The Devine Adventures Team</strong></p>
      </div>
      <div style="background-color: #F8F9FA; border-top: 1px solid #E9ECEF; padding: 16px; text-align: center; font-size: 12px; color: #6B7280;">
        &copy; Devine Adventures. All rights reserved.
      </div>
    </div>
    """
    return send_email(booking.traveler_email, subject, html_content)


def run_review_request_job(app):
    """
    Daily job: find all confirmed bookings whose end date has passed,
    mark them 'completed', and send review request emails.
    """
    with app.app_context():
        from app.extensions import db
        from app.models import Booking, TourDate

        today = date.today()
        logger.info(f"[Scheduler] Running review request job for date: {today}")

        # Find confirmed bookings whose tour has already ended
        eligible = (
            Booking.query
            .join(TourDate, Booking.tour_date_id == TourDate.id)
            .filter(
                Booking.status == 'confirmed',
                Booking.review_request_sent == False,
                TourDate.end_date < today
            )
            .all()
        )

        logger.info(f"[Scheduler] Found {len(eligible)} bookings eligible for review requests.")

        for booking in eligible:
            try:
                booking.status = 'completed'
                booking.review_request_sent = True
                db.session.add(booking)
                db.session.flush()

                send_review_request_email(booking)
                logger.info(f"[Scheduler] Review request sent to {booking.traveler_email} (Ref: {booking.booking_reference})")
            except Exception as e:
                logger.error(f"[Scheduler] Failed to process booking {booking.booking_reference}: {e}")
                db.session.rollback()

        db.session.commit()
        logger.info("[Scheduler] Review request job complete.")
