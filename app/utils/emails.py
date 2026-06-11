import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configure logging
logger = logging.getLogger(__name__)


def send_email(to_email, subject, html_content):
    """
    Sends an email using the SendGrid API client.
    Falls back to console/logging if SendGrid credentials are not available.
    """
    api_key = os.environ.get('SENDGRID_API_KEY')
    sender = os.environ.get('SENDGRID_SENDER', 'noreply@devineadventures.com')

    if not api_key:
        logger.warning("SENDGRID_API_KEY not set in environment.")
        print("=" * 60)
        print("MOCK EMAIL SENT (Development mode)")
        print(f"To: {to_email}")
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(html_content)
        print("=" * 60)
        return True

    try:
        message = Mail(
            from_email=sender,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        sg = SendGridAPIClient(api_key)
        sg.send(message)
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via SendGrid: {str(e)}")
        # Print fallback in case of errors during development/testing
        print("=" * 60)
        print("SENDGRID ERROR - FALLBACK EMAIL DUMP")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(html_content)
        print("=" * 60)
        return False


def send_booking_confirmation(booking):
    """
    Sends a booking confirmation email to the traveler with booking reference,
    tour details, meeting point, and what to bring.
    """
    subject = f"Booking Confirmed: {booking.tour.title} [Ref: {booking.booking_reference}]"
    
    # Generate what to bring based on category
    what_to_bring_map = {
        'hiking': "Sturdy hiking boots, rain jacket, water bottle, backpack, sun protection, energy snacks.",
        'safari': "Comfortable light clothing, sun hat, sunglasses, binoculars, camera, warm jacket for early morning.",
        'mountain_climbing': "Thermal layers, mountaineering boots, sleeping bag, headlamp, hiking poles, gloves, beanie.",
        'water_sports': "Swimwear, towel, quick-dry clothes, sunscreen, water shoes, change of clothes.",
        'cultural': "Comfortable walking shoes, respectful clothing, camera, small bag for personal items.",
    }
    what_to_bring = what_to_bring_map.get(booking.tour.category, "Comfortable clothes, walking shoes, water bottle, sunscreen.")

    html_content = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #111827; max-width: 600px; margin: 0 auto; border: 1px solid #E9ECEF; border-radius: 8px; overflow: hidden;">
      <div style="background-color: #1B4332; padding: 24px; text-align: center; color: white;">
        <h1 style="margin: 0; font-size: 24px;">Adventure Awaits!</h1>
        <p style="margin: 8px 0 0; font-size: 16px; opacity: 0.9;">Your booking is confirmed.</p>
      </div>
      <div style="padding: 24px;">
        <p>Dear {booking.traveler_name},</p>
        <p>Thank you for booking with <strong>Devine Adventures</strong>. We are thrilled to host you on this unforgettable journey. Below are your booking details:</p>
        
        <div style="background-color: #FAFAFA; border: 1px solid #E9ECEF; border-radius: 6px; padding: 16px; margin: 20px 0;">
          <h3 style="margin-top: 0; color: #1B4332;">Booking Reference: {booking.booking_reference}</h3>
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding: 6px 0; font-weight: bold; width: 120px;">Tour:</td>
              <td style="padding: 6px 0;">{booking.tour.title}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; font-weight: bold;">Date:</td>
              <td style="padding: 6px 0;">{booking.tour_date.start_date.strftime('%B %d, %Y')} to {booking.tour_date.end_date.strftime('%B %d, %Y')}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; font-weight: bold;">Participants:</td>
              <td style="padding: 6px 0;">{booking.num_guests} traveler(s)</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; font-weight: bold;">Total Price:</td>
              <td style="padding: 6px 0;">KES {booking.total_price_kes:,.2f} / USD {booking.total_price_usd:,.2f}</td>
            </tr>
          </table>
        </div>

        <div style="margin-bottom: 20px;">
          <h4 style="color: #1B4332; margin-bottom: 8px;">📍 Meeting Point & Time</h4>
          <p style="margin: 0;">{booking.tour.meeting_point or 'To be communicated by the operator before departure.'}</p>
        </div>

        <div style="margin-bottom: 20px;">
          <h4 style="color: #1B4332; margin-bottom: 8px;">🎒 What to Bring</h4>
          <p style="margin: 0; background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 10px; border-radius: 0 4px 4px 0;">
            {what_to_bring}
          </p>
        </div>

        <p>If you need to change or cancel your booking, you can manage it directly from your <a href="#" style="color: #E85D04; text-decoration: underline;">Traveler Dashboard</a>.</p>
        
        <p style="margin-top: 30px;">Warm regards,<br><strong>The Devine Adventures Team</strong></p>
      </div>
      <div style="background-color: #FAFAFA; border-top: 1px solid #E9ECEF; padding: 16px; text-align: center; font-size: 12px; color: #6B7280;">
        &copy; {datetime_year()} Devine Adventures. All rights reserved.
      </div>
    </div>
    """
    return send_email(booking.traveler_email, subject, html_content)


def send_waitlist_notification(waitlist_entry):
    """
    Notifies a traveler on the waitlist that a spot has opened up and invites them to book.
    """
    subject = f"Spot Opened! {waitlist_entry.tour_date.tour.title} is available"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #111827; max-width: 600px; margin: 0 auto; border: 1px solid #E9ECEF; border-radius: 8px; overflow: hidden;">
      <div style="background-color: #E85D04; padding: 24px; text-align: center; color: white;">
        <h1 style="margin: 0; font-size: 24px;">Good News!</h1>
        <p style="margin: 8px 0 0; font-size: 16px; opacity: 0.9;">A spot has opened up on your desired date.</p>
      </div>
      <div style="padding: 24px;">
        <p>Dear {waitlist_entry.name},</p>
        <p>We are pleased to inform you that a spot has just opened up for <strong>{waitlist_entry.tour_date.tour.title}</strong> departing on <strong>{waitlist_entry.tour_date.start_date.strftime('%B %d, %Y')}</strong>.</p>
        
        <p>Since you joined our waitlist, we wanted to give you the first opportunity to book this adventure. Spots are filled on a first-come, first-served basis, so act quickly!</p>
        
        <div style="text-align: center; margin: 30px 0;">
          <a href="#" style="background-color: #1B4332; color: white; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 6px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">Book Your Spot Now</a>
        </div>
        
        <p>If you have any questions or require assistance, please reply to this email.</p>
        
        <p style="margin-top: 30px;">Happy exploring,<br><strong>The Devine Adventures Team</strong></p>
      </div>
      <div style="background-color: #FAFAFA; border-top: 1px solid #E9ECEF; padding: 16px; text-align: center; font-size: 12px; color: #6B7280;">
        &copy; {datetime_year()} Devine Adventures. All rights reserved.
      </div>
    </div>
    """
    return send_email(waitlist_entry.email, subject, html_content)


def datetime_year():
    from datetime import datetime
    return datetime.now().year
