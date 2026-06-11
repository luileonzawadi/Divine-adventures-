import logging
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app.models import Payment, Booking, Tour
from app.extensions import db

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

EXCHANGE_RATE = 130.0  # 1 USD = 130 KES


@admin_bp.route('/admin/revenue')
@login_required
def revenue():
    """
    Renders the admin revenue dashboard compiling completed payments stats.
    """
    if current_user.role != 'admin':
        abort(403, description="Access restricted to administrators.")

    completed_payments = Payment.query.filter_by(status='completed').order_by(Payment.created_at.desc()).all()

    # Base metrics
    stripe_count = 0
    stripe_total = 0.0
    mpesa_count = 0
    mpesa_total = 0.0

    # Aggregates
    tour_stats = {}
    monthly_stats = {}

    for payment in completed_payments:
        amount = float(payment.amount)
        currency = payment.currency.upper()
        method = payment.method.lower()

        # Method level tracking
        if method == 'stripe':
            stripe_count += 1
            stripe_total += amount
        elif method == 'mpesa':
            mpesa_count += 1
            mpesa_total += amount

        # Tour level aggregation
        tour_title = payment.booking.tour.title if (payment.booking and payment.booking.tour) else "Deleted/Unknown Tour"
        if tour_title not in tour_stats:
            tour_stats[tour_title] = {
                'kes': 0.0,
                'usd': 0.0,
                'combined_usd': 0.0,
                'count': 0
            }
        tour_stats[tour_title]['count'] += 1
        if currency == 'KES':
            tour_stats[tour_title]['kes'] += amount
            tour_stats[tour_title]['combined_usd'] += amount / EXCHANGE_RATE
        else:
            tour_stats[tour_title]['usd'] += amount
            tour_stats[tour_title]['combined_usd'] += amount

        # Month level aggregation
        month_key = payment.created_at.strftime('%Y-%m')
        month_name = payment.created_at.strftime('%B %Y')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                'name': month_name,
                'kes': 0.0,
                'usd': 0.0,
                'combined_kes': 0.0,
                'count': 0
            }
        monthly_stats[month_key]['count'] += 1
        if currency == 'KES':
            monthly_stats[month_key]['kes'] += amount
            monthly_stats[month_key]['combined_kes'] += amount
        else:
            monthly_stats[month_key]['usd'] += amount
            monthly_stats[month_key]['combined_kes'] += amount * EXCHANGE_RATE

    # Overall Unified Totals
    unified_kes = mpesa_total + (stripe_total * EXCHANGE_RATE)
    unified_usd = stripe_total + (mpesa_total / EXCHANGE_RATE)

    # Sort monthly stats chronologically descending
    sorted_monthly = [v for k, v in sorted(monthly_stats.items(), reverse=True)]

    return render_template(
        'admin/revenue.html',
        payments=completed_payments,
        stripe_count=stripe_count,
        stripe_total=stripe_total,
        mpesa_count=mpesa_count,
        mpesa_total=mpesa_total,
        unified_kes=unified_kes,
        unified_usd=unified_usd,
        tour_stats=tour_stats,
        monthly_stats=sorted_monthly,
        exchange_rate=EXCHANGE_RATE
    )
