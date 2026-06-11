import os
import sys
from datetime import datetime, date, timedelta, timezone

# Add parent directory to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.extensions import db
from app.models import User, TourOperator, Tour, TourDate, Itinerary

def seed():
    # Remove existing db if it exists
    db_path = os.path.join('instance', 'devine_adventures.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database file.")

    app = create_app('development')
    with app.app_context():
        # Recreate all tables
        db.create_all()
        print("Recreated database tables successfully.")

        # Create traveler
        traveler = User(
            email='traveler@devine.com',
            username='traveler',
            first_name='John',
            last_name='Traveler',
            phone='+254712345678',
            role='traveler'
        )
        traveler.set_password('password')
        db.session.add(traveler)

        # Create operator user
        operator_user = User(
            email='operator@devine.com',
            username='operator',
            first_name='Alice',
            last_name='Operator',
            phone='+254722222222',
            role='operator'
        )
        operator_user.set_password('password')
        db.session.add(operator_user)
        db.session.flush()  # get operator_user.id

        # Create operator profile
        operator_profile = TourOperator(
            user_id=operator_user.id,
            company_name='Savannah Adventures Ltd',
            description='Premier local tour guides and wildlife experts in East Africa.',
            logo_url='https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=150',
            license_number='OP-294029',
            location='Nairobi, Kenya',
            website='www.savannahadventures.com',
            is_verified=True,
            rating=4.8,
            total_tours=5
        )
        db.session.add(operator_profile)
        db.session.flush()

        # Create admin
        admin = User(
            email='admin@devine.com',
            username='admin',
            first_name='Admin',
            last_name='Boss',
            phone='+254733333333',
            role='admin'
        )
        admin.set_password('password')
        db.session.add(admin)

        # Create Tour 1: 30% Deposit Safari
        safari_tour = Tour(
            operator_id=operator_profile.id,
            title='3-Day Masai Mara Wild Safari',
            slug='3-day-masai-mara-wild-safari',
            description='Witness the incredible Great Migration and spot the Big Five in Kenya\'s premier wildlife reserve.',
            short_description='Spot lions, leopards, rhinos, elephants, and buffaloes in the legendary Masai Mara.',
            duration_days=3,
            difficulty='moderate',
            max_group_size=12,
            price_kes=65000.00,
            price_usd=500.00,
            location='Masai Mara National Reserve',
            meeting_point='Nairobi CBD, outside Hilton Hotel Lobby at 6:30 AM',
            category='safari',
            included_items='Transport in open-roof 4x4 safari cruiser\nPark entry fees\nProfessional local safari guide\nAll meals and drinking water\nLodge accommodation',
            excluded_items='Tips and gratuities\nTravel insurance\nAlcoholic drinks\nOptional balloon safari (USD 450)',
            cover_image_url='https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=800',
            is_featured=True,
            deposit_percent=30
        )
        db.session.add(safari_tour)
        db.session.flush()

        # Tour 1 Date
        date1 = TourDate(
            tour_id=safari_tour.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            max_capacity=12,
            current_bookings=0
        )
        db.session.add(date1)

        # Tour 1 Itinerary
        day1 = Itinerary(
            tour_id=safari_tour.id,
            day_number=1,
            title='Drive to Masai Mara & Afternoon Game Drive',
            description='Depart Nairobi early morning, drive through the Great Rift Valley, and arrive at the Mara in time for lunch and an afternoon game drive.',
            highlights='Great Rift Valley Viewpoint, Afternoon Game Drive',
            accommodation='Mara Wildlife Lodge',
            meals_included='Lunch, Dinner'
        )
        day2 = Itinerary(
            tour_id=safari_tour.id,
            day_number=2,
            title='Full Day Game Drive in the Reserve',
            description='Spend the entire day exploring the plains looking for predators, lions, leopards, and large elephant herds.',
            highlights='Mara River crossing point, Big Five tracking',
            accommodation='Mara Wildlife Lodge',
            meals_included='Breakfast, Lunch, Dinner'
        )
        db.session.add(day1)
        db.session.add(day2)

        # Create Tour 2: 100% Payment Mountain Climb
        mountain_tour = Tour(
            operator_id=operator_profile.id,
            title='Mount Kenya Summit Challenge',
            slug='mount-kenya-summit-challenge',
            description='Hike up Point Lenana (4,985m) via the scenic Chogoria Route and descent down the Sirimon Route.',
            short_description='Conquer the second-highest peak in Africa with professional alpine guides.',
            duration_days=5,
            difficulty='hard',
            max_group_size=8,
            price_kes=45000.00,
            price_usd=350.00,
            location='Mount Kenya National Park',
            meeting_point='Nairobi National Museum Parking Lot at 7:30 AM',
            category='mountain_climbing',
            included_items='Mountain park fees\nExperienced mountain guides and porters\nAll meals on the mountain\nTents and cooking gear\nRescue fees',
            excluded_items='Sleeping bag and climbing gear\nPersonal warm clothing\nTips for porters and guides\nSoft drinks',
            cover_image_url='https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?w=800',
            is_featured=False,
            deposit_percent=100
        )
        db.session.add(mountain_tour)
        db.session.flush()

        # Tour 2 Date
        date2 = TourDate(
            tour_id=mountain_tour.id,
            start_date=date.today() + timedelta(days=45),
            end_date=date.today() + timedelta(days=49),
            max_capacity=8,
            current_bookings=0
        )
        db.session.add(date2)

        # Commit everything
        db.session.commit()
        print("Database successfully seeded with default users, operator, and tours!")

if __name__ == '__main__':
    seed()
