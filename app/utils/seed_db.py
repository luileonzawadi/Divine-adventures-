import os
import sys
from datetime import datetime, date, timedelta, timezone

# Add parent directory to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.extensions import db
from app.models import User, TourOperator, Tour, TourDate, Itinerary, Review, ReviewPhoto

def seed():
    app = create_app('development')
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
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

        # Create some other travelers for reviews
        reviewers = [
            User(email='mercy@gmail.com', username='mercy', first_name='Mercy', last_name='Githaiga', phone='+254711111111', role='traveler'),
            User(email='kevin@gmail.com', username='kevin', first_name='Kevin', last_name='Mwangi', phone='+254722111111', role='traveler'),
            User(email='sara@gmail.com', username='sara', first_name='Sara', last_name='Achieng', phone='+254733111111', role='traveler'),
        ]
        for r in reviewers:
            r.set_password('password')
            db.session.add(r)

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
        db.session.flush()

        # Create operator profile
        operator_profile = TourOperator(
            user_id=operator_user.id,
            company_name='Devine Adventure Guides',
            description='Professional local guides and trekking experts in Kenya.',
            logo_url='/static/logo.png',
            license_number='OP-294029',
            location='Nairobi, Kenya',
            website='www.devineadventures.co.ke',
            is_verified=True,
            rating=4.9,
            total_tours=6
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

        # Define the tours
        tours_data = [
            {
                "title": "Tigoni Tea Highlands & Waterfalls Walk",
                "slug": "tigoni-tea-highlands-waterfalls-walk",
                "description": "Escape the city and wander through the lush green tea fields of Tigoni. This beginner-friendly walk leads to a beautiful hidden waterfall, serene forests, and a refreshing outdoor picnic. Perfect for meeting new friends and enjoying clean fresh air.",
                "short_description": "Walk through serene tea plantations and discover a hidden waterfall in Tigoni.",
                "duration_days": 1,
                "difficulty": "easy",
                "max_group_size": 25,
                "price_kes": 2500.00,
                "price_usd": 20.00,
                "location": "Tigoni, Limuru",
                "meeting_point": "Bata Hilton CBD at 7:30 AM",
                "category": "hiking",
                "included_items": "Professional hiking guides\nGuided tea farm walkthrough\nCommunity & guide entry fees\nFirst aid and safety support\n1 Liter drinking water",
                "excluded_items": "Transport (Self-drive or carpool options available)\nLunch / Snacks (available for purchase)\nTips and gratuities",
                "cover_image_url": "/static/images/adventure_1.jpeg",
                "is_featured": True,
                "deposit_percent": 100,
                "itinerary": [
                    {"day": 1, "title": "Farm Arrival & Trek to Waterfalls", "desc": "Meet at Limuru at 8:30 AM. Begin the hike through private tea fields, descending down to the beautiful waterfalls for pictures and a relaxed picnic. Return by 1:30 PM.", "highlights": "Tea highlands walk, Hidden waterfalls, Picnic ground", "accommodation": "", "meals": ""}
                ],
                "dates": [
                    {"days_offset": 6, "capacity": 25, "booked": 18},
                    {"days_offset": 13, "capacity": 25, "booked": 5},
                    {"days_offset": 20, "capacity": 25, "booked": 0}
                ]
            },
            {
                "title": "Kijabe Forest & Railway Line Trek",
                "slug": "kijabe-forest-railway-line-trek",
                "description": "An adventure back in time! Follow the historic railway line through old dark tunnels, climb up into the lush Kijabe forest, and view the stunning Great Rift Valley floor. This moderate hike includes river crossings and exploring old colonial railway ruins.",
                "short_description": "Trek along the historic Rift Valley railway, dark tunnels, and beautiful waterfalls.",
                "duration_days": 1,
                "difficulty": "moderate",
                "max_group_size": 20,
                "price_kes": 3200.00,
                "price_usd": 25.00,
                "location": "Kijabe, Rift Valley",
                "meeting_point": "Nairobi National Museum Parking at 6:45 AM",
                "category": "hiking",
                "included_items": "Roundtrip transport from Nairobi\nForest entry permits\nProfessional guides & security\nDrinking water\nGroup photos",
                "excluded_items": "Lunch/Personal snacks (bring pocket lunch)\nTips\nTravel insurance",
                "cover_image_url": "/static/images/adventure_2.jpeg",
                "is_featured": True,
                "deposit_percent": 100,
                "itinerary": [
                    {"day": 1, "title": "Tunnels walk and Waterfall Climb", "desc": "Depart Nairobi early. Begin walking from the hot Rift valley floor, through colonial-era railway tunnels (bring a flashlight!), up to the Kijabe forest waterfalls. Finish by late afternoon.", "highlights": "Railway tunnels, River crossing, Deep forest trek", "accommodation": "", "meals": ""}
                ],
                "dates": [
                    {"days_offset": 7, "capacity": 20, "booked": 19},
                    {"days_offset": 14, "capacity": 20, "booked": 8}
                ]
            },
            {
                "title": "Aberdare Elephant Hill Challenge",
                "slug": "aberdare-elephant-hill-challenge",
                "description": "Test your endurance on one of Kenya's most famous and demanding hiking trails. Trek through dense bamboo forests, steep clay slopes, sub-alpine moorlands, and rock scramble up to the summit of Elephant Hill (3,700m). Outstanding views of the Aberdare range await the brave.",
                "short_description": "Conquer the famous Elephant Hill in the Aberdares. High altitude, bamboo forests.",
                "duration_days": 1,
                "difficulty": "hard",
                "max_group_size": 15,
                "price_kes": 4500.00,
                "price_usd": 35.00,
                "location": "Aberdare National Park",
                "meeting_point": "Nairobi CBD, Kencom House at 5:30 AM",
                "category": "hiking",
                "included_items": "Transport in custom safari bus\nKFS entry fees & ranger escort\nExperienced mountain guides\nSnack pack and water\nFirst aid & oximeter tracking",
                "excluded_items": "Extra warm clothing / rain gear\nLunch\nTips for rangers and guides",
                "cover_image_url": "/static/images/adventure_3.jpeg",
                "is_featured": True,
                "deposit_percent": 100,
                "itinerary": [
                    {"day": 1, "title": "The Bamboo Gate to Summit", "desc": "Start the climb from njabini forest station. Navigate the challenging 'Point Despair' and push through moorland to the Elephant Hill summit. Head back down to the gate by 4:00 PM.", "highlights": "Bamboo canopy, Point Despair, Alpine Moorlands", "accommodation": "", "meals": ""}
                ],
                "dates": [
                    {"days_offset": 8, "capacity": 15, "booked": 14},
                    {"days_offset": 22, "capacity": 15, "booked": 2}
                ]
            },
            {
                "title": "Mount Longonot Crater Hike",
                "slug": "mount-longonot-crater-hike",
                "description": "Climb the steep volcanic slopes of Mount Longonot, hike around the massive 7.2km crater rim, and enjoy panoramic views of Lake Naivasha and the Rift Valley floor. Spot wildlife such as zebras, giraffes, and antelopes grazing in the park below.",
                "short_description": "Hike up an active volcano and walk around the scenic 7.2km crater rim.",
                "duration_days": 1,
                "difficulty": "moderate",
                "max_group_size": 30,
                "price_kes": 3000.00,
                "price_usd": 24.00,
                "location": "Mount Longonot National Park",
                "meeting_point": "Hilton Lobby CBD at 6:30 AM",
                "category": "hiking",
                "included_items": "Roundtrip transport in tour bus\nPark entry fees\nExperienced lead guide\nSecurity ranger escort\nFirst aid kit support",
                "excluded_items": "Lunch (carry packed lunch)\nTips\nAdditional mineral water (bring 3L)",
                "cover_image_url": "/static/images/adventure_4.jpeg",
                "is_featured": False,
                "deposit_percent": 100,
                "itinerary": [
                    {"day": 1, "title": "Summit Climb & Crater Rim Loop", "desc": "Arrive at the park gate, hike 3.1km up the steep ridge to the crater rim, then hike the challenging 7.2km loop around the rim. Return to Nairobi by 5:00 PM.", "highlights": "Volcanic crater, Rift valley views, Wildlife sightings", "accommodation": "", "meals": ""}
                ],
                "dates": [
                    {"days_offset": 15, "capacity": 30, "booked": 25}
                ]
            },
            {
                "title": "Keriita Forest Waterfall & Zip-lining",
                "slug": "keriita-forest-waterfall-zip-lining",
                "description": "Enjoy a double-dose of adrenaline! Walk through the towering trees of Keriita forest to a spectacular waterfall, then fly high above the canopy on East Africa's longest zip-lines. This beginner-friendly hike combines beautiful scenery with high-flying action.",
                "short_description": "A scenic forest trek coupled with a thrilling zip-lining flight over the forest canopy.",
                "duration_days": 1,
                "difficulty": "easy",
                "max_group_size": 20,
                "price_kes": 5500.00,
                "price_usd": 45.00,
                "location": "Kimende, Lari",
                "meeting_point": "National Museum Nairobi at 7:30 AM",
                "category": "hiking",
                "included_items": "Transport to and from Kimende\nForest entry & guide fees\n2 lines Zip-lining experience fee\nForest rangers escort\nProfessional photographer",
                "excluded_items": "Lunch / Drinks at the lodge\nTips\nAdditional zip-line runs",
                "cover_image_url": "/static/images/adventure_5.jpeg",
                "is_featured": True,
                "deposit_percent": 50,
                "itinerary": [
                    {"day": 1, "title": "Forest Trek and Zip-line Flight", "desc": "Trek through the indigenous forest to Keriita Waterfall. Head back to the forest adventure center for safety briefing and zip-lining. Afternoon departure to Nairobi.", "highlights": "Waterfalls, 2-line zip-lining, Forest adventure center", "accommodation": "", "meals": ""}
                ],
                "dates": [
                    {"days_offset": 9, "capacity": 20, "booked": 15},
                    {"days_offset": 23, "capacity": 20, "booked": 4}
                ]
            },
            {
                "title": "Karura Forest Bike & Trail Walk",
                "slug": "karura-forest-bike-trail-walk",
                "description": "Spend a relaxing morning cycling along the designated trails of Karura Forest. We'll explore the Mau Mau caves, the waterfalls, and the peaceful bamboo paths on two wheels. A great city escape without leaving Nairobi.",
                "short_description": "A leisurely bicycle ride and walk through Nairobi's urban green lung.",
                "duration_days": 1,
                "difficulty": "easy",
                "max_group_size": 15,
                "price_kes": 2000.00,
                "price_usd": 16.00,
                "location": "Karura Forest, Nairobi",
                "meeting_point": "Limuru Road Gate A at 8:30 AM",
                "category": "cycling",
                "included_items": "Bicycle rental for 2 hours\nKarura Forest entry fees\nCycling guide and instructor\nFresh water bottle",
                "excluded_items": "Transport (Self-drive to gate)\nLunch and snacks\nTips",
                "cover_image_url": "/static/images/adventure_6.jpeg",
                "is_featured": False,
                "deposit_percent": 100,
                "itinerary": [
                    {"day": 1, "title": "Cycling Karura Trails", "desc": "Pick up bikes at Gate A. Cycle through key trails visiting the Mau Mau caves, waterfalls, and a relaxing picnic in the garden area. Return bikes and wrap up.", "highlights": "Karura waterfall, Mau Mau caves, Bamboo forest path", "accommodation": "", "meals": ""}
                ],
                "dates": [
                    {"days_offset": 5, "capacity": 15, "booked": 10},
                    {"days_offset": 12, "capacity": 15, "booked": 12},
                    {"days_offset": 19, "capacity": 15, "booked": 0}
                ]
            }
        ]

        # Add tours and dates
        today_val = date.today()
        seeded_tours = []
        for t_info in tours_data:
            tour = Tour(
                operator_id=operator_profile.id,
                title=t_info["title"],
                slug=t_info["slug"],
                description=t_info["description"],
                short_description=t_info["short_description"],
                duration_days=t_info["duration_days"],
                difficulty=t_info["difficulty"],
                max_group_size=t_info["max_group_size"],
                price_kes=t_info["price_kes"],
                price_usd=t_info["price_usd"],
                location=t_info["location"],
                meeting_point=t_info["meeting_point"],
                category=t_info["category"],
                included_items=t_info["included_items"],
                excluded_items=t_info["excluded_items"],
                cover_image_url=t_info["cover_image_url"],
                is_featured=t_info["is_featured"],
                deposit_percent=t_info["deposit_percent"]
            )
            db.session.add(tour)
            db.session.flush()
            seeded_tours.append((tour, t_info))

            # Add itinerary
            for itin_day in t_info["itinerary"]:
                itinerary_day = Itinerary(
                    tour_id=tour.id,
                    day_number=itin_day["day"],
                    title=itin_day["title"],
                    description=itin_day["desc"],
                    highlights=itin_day["highlights"],
                    accommodation=itin_day["accommodation"],
                    meals_included=itin_day["meals"]
                )
                db.session.add(itinerary_day)

            # Add dates
            for dt in t_info["dates"]:
                tour_date = TourDate(
                    tour_id=tour.id,
                    start_date=today_val + timedelta(days=dt["days_offset"]),
                    end_date=today_val + timedelta(days=dt["days_offset"] + t_info["duration_days"] - 1),
                    max_capacity=dt["capacity"],
                    current_bookings=dt["booked"]
                )
                db.session.add(tour_date)

        db.session.commit()

        # Seed reviews
        reviews_data = [
            {
                "user": reviewers[0], # Mercy
                "tour_slug": "tigoni-tea-highlands-waterfalls-walk",
                "rating": 5,
                "title": "Unbelievably beautiful and relaxing!",
                "comment": "Exceptional and affordable outdoor experiences showcasing the best of Kenya's outdoors. The tea farms in Tigoni were so lush and peaceful. The guide was extremely professional, and I met so many adventurous folks. Highly recommend!",
                "photos": ["/static/images/adventure_7.jpeg", "/static/images/adventure_8.jpeg"]
            },
            {
                "user": reviewers[1], # Kevin
                "tour_slug": "kijabe-forest-railway-line-trek",
                "rating": 5,
                "title": "Challenging but worth it!",
                "comment": "Walking through the old railway tunnels was such a thrill! The waterfalls in Kijabe forest were breathtaking. Guides were top tier and made sure everyone stayed safe.",
                "photos": ["/static/images/adventure_9.jpeg"]
            },
            {
                "user": reviewers[2], # Sara
                "tour_slug": "aberdare-elephant-hill-challenge",
                "rating": 4,
                "title": "An intense climb but stunning summit!",
                "comment": "Elephant hill is no joke! Point Despair lives up to its name, but standing at the summit (3700m) is an unforgettable feeling. Make sure you pack warm and waterproof clothes.",
                "photos": ["/static/images/adventure_10.jpeg", "/static/images/adventure_11.jpeg"]
            }
        ]

        for rev_info in reviews_data:
            tour = Tour.query.filter_by(slug=rev_info["tour_slug"]).first()
            if tour:
                review = Review(
                    user_id=rev_info["user"].id,
                    tour_id=tour.id,
                    rating=rev_info["rating"],
                    title=rev_info["title"],
                    comment=rev_info["comment"],
                    is_approved=True
                )
                db.session.add(review)
                db.session.flush()

                # Add photos
                for photo_url in rev_info["photos"]:
                    photo = ReviewPhoto(
                        review_id=review.id,
                        image_url=photo_url
                    )
                    db.session.add(photo)

        db.session.commit()
        print("Database successfully seeded with new local adventure hikes, dates, and photo reviews!")

if __name__ == '__main__':
    seed()
