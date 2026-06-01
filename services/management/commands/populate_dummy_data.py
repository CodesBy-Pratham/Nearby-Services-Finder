import math
import random

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from accounts.models import User
from services.models import Category, Service


CATEGORIES = [
    "Plumber",
    "Electrician",
    "Doctor",
    "Dentist",
    "Mechanic",
    "Salon",
    "Grocery",
    "Pharmacy",
    "Restaurant",
    "Gym",
]


def random_point_within_radius(center_lat, center_lng, max_km):
    """Return (lat, lng) randomly distributed within max_km of center."""
    # Random distance (square-root for uniform area distribution)
    r = max_km * math.sqrt(random.random())
    angle = random.uniform(0, 2 * math.pi)
    # 1 degree latitude ≈ 111.32 km
    delta_lat = (r * math.cos(angle)) / 111.32
    # 1 degree longitude varies with latitude
    delta_lng = (r * math.sin(angle)) / (111.32 * math.cos(math.radians(center_lat)))
    return center_lat + delta_lat, center_lng + delta_lng


class Command(BaseCommand):
    help = "Populate the database with dummy service data spread across a map area."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lat",
            type=float,
            default=19.987026,
            help="Center latitude (default: Mumbai)",
        )
        parser.add_argument(
            "--lng",
            type=float,
            default=73.784008,
            help="Center longitude (default: Mumbai)",
        )
        parser.add_argument(
            "--spread-km",
            type=float,
            default=25.0,
            help="Max spread radius in km (default: 25)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=200,
            help="Number of services to create (default: 200)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing services before seeding",
        )

    def handle(self, *args, **options):
        center_lat = options["lat"]
        center_lng = options["lng"]
        spread_km = options["spread_km"]
        count = options["count"]

        if options["clear"]:
            deleted, _ = Service.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted {deleted} existing services.")
            )

        # Create categories
        categories = []
        for name in CATEGORIES:
            cat, created = Category.objects.get_or_create(name=name)
            categories.append(cat)
            if created:
                self.stdout.write(f"  Created category: {name}")

        # Create staff user for seeding
        staff_user, created = User.objects.get_or_create(
            username="staff_seeder",
            defaults={"role": "STAFF", "email": "seeder@example.com"},
        )
        if created:
            staff_user.set_password("seed1234")
            staff_user.save()
            self.stdout.write(f"  Created staff user: staff_seeder / seed1234")

        # Bulk-create services
        services = []
        for i in range(1, count + 1):
            lat, lng = random_point_within_radius(center_lat, center_lng, spread_km)
            category = random.choice(categories)
            services.append(
                Service(
                    name=f"{category.name} Service #{i}",
                    category=category,
                    location=Point(lng, lat, srid=4326),
                    rating=round(random.uniform(1.0, 5.0), 1),
                    created_by=staff_user,
                )
            )

        Service.objects.bulk_create(services)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Inserted {count} services within {spread_km} km of ({center_lat}, {center_lng})."
            )
        )
        self.stdout.write(
            f"\nTest it:\n"
            f"  5 km radius:  GET /api/services/services/nearby/?lat={center_lat}&lng={center_lng}&radius=5\n"
            f"  25 km radius: GET /api/services/services/nearby/?lat={center_lat}&lng={center_lng}&radius={spread_km}\n"
            f"  By category:  GET /api/services/services/nearby/?lat={center_lat}&lng={center_lng}&radius=10&category=Doctor\n"
        )
