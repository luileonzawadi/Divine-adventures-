import os
import time
import base64
import logging
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


def format_phone_number(phone):
    """
    Format phone number to MSISDN format (2547XXXXXXXX or 2541XXXXXXXX).
    """
    # Keep only digits
    cleaned = "".join(c for c in phone if c.isdigit())
    if cleaned.startswith("0"):
        cleaned = "254" + cleaned[1:]
    elif cleaned.startswith("254"):
        pass
    else:
        # Default fallback to appending 254 if not present
        if len(cleaned) == 9:
            cleaned = "254" + cleaned
        elif len(cleaned) > 9:
            cleaned = "254" + cleaned[-9:]
        else:
            cleaned = "254" + cleaned
    return cleaned


class MpesaConnector:
    def __init__(self, consumer_key=None, consumer_secret=None, shortcode=None, passkey=None, callback_url=None):
        self.consumer_key = consumer_key or os.environ.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = consumer_secret or os.environ.get('MPESA_CONSUMER_SECRET')
        self.shortcode = shortcode or os.environ.get('MPESA_SHORTCODE', '174379')
        self.passkey = passkey or os.environ.get('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
        self.callback_url = callback_url or os.environ.get('MPESA_CALLBACK_URL')

    def is_configured(self):
        """Checks if M-Pesa API credentials are set in environment."""
        return bool(self.consumer_key and self.consumer_secret and self.callback_url)

    def get_access_token(self):
        """
        Retrieves OAuth2 access token from Safaricom.
        Falls back to a mock token if credentials are not configured.
        """
        if not self.is_configured():
            logger.info("M-Pesa credentials not configured. Using simulated access token.")
            return "mock_access_token"

        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(url, auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret), timeout=10)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logger.error(f"M-Pesa auth failed: {response.text}")
                raise Exception(f"Failed to fetch access token: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching access token: {str(e)}")
            raise e

    def initiate_stk_push(self, phone, amount, booking_reference):
        """
        Initiates an M-Pesa Daraja STK Push (Lipa Na M-Pesa Online).
        """
        formatted_phone = format_phone_number(phone)
        # Safaricom amount must be integer
        amount_int = int(round(float(amount)))

        if not self.is_configured():
            # Simulation Mode
            mock_checkout_id = f"ws_CO_mock_{int(time.time())}_{booking_reference}"
            logger.info(f"[M-PESA SIMULATION] STK Push initiated. Phone: {formatted_phone}, Amount: {amount_int}, Booking: {booking_reference}")
            logger.info(f"[M-PESA SIMULATION] Simulated Callback URL will be triggered with CheckoutRequestID: {mock_checkout_id}")
            return {
                "ResponseCode": "0",
                "ResponseDescription": "Success. Request accepted for processing",
                "MerchantRequestID": f"mock_merch_{booking_reference}",
                "CheckoutRequestID": mock_checkout_id,
                "simulation": True
            }

        access_token = self.get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare callback URL with booking_ref query parameter for robust callback routing
        callback_url_with_ref = f"{self.callback_url}?booking_ref={booking_reference}"

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount_int,
            "PartyA": formatted_phone,
            "PartyB": self.shortcode,
            "PhoneNumber": formatted_phone,
            "CallBackURL": callback_url_with_ref,
            "AccountReference": booking_reference,
            "TransactionDesc": f"Deposit for Tour Booking {booking_reference}"
        }

        try:
            url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                logger.info(f"M-Pesa STK Push initiated successfully for {booking_reference}")
                return response.json()
            else:
                logger.error(f"M-Pesa STK Push request failed: {response.text}")
                return {
                    "ResponseCode": str(response.status_code),
                    "ResponseDescription": response.text,
                    "error": True
                }
        except Exception as e:
            logger.error(f"Exception during M-Pesa STK Push: {str(e)}")
            return {
                "ResponseCode": "500",
                "ResponseDescription": str(e),
                "error": True
            }
