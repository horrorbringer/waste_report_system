"""Seed initial categories, users (admin & residents), and sample waste reports."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.database import Base, SessionLocal, engine, ensure_schema_columns
from app.models import Category, StatusHistory, User, WasteReport
from app.security import hash_password

DEFAULT_CATEGORIES = [
    (
        "Plastic Waste",
        "សំណល់ប្លាស្ទិក",
        "Discarded plastic bottles, bags, packaging, and single-use containers.",
        "ដបប្លាស្ទិក ថង់ប្លាស្ទិក កញ្ចប់វេចខ្ចប់ និងប្រអប់ប្រើប្រាស់តែម្តង។",
    ),
    (
        "Organic Waste",
        "សំណល់សរីរាង្គ",
        "Food scraps, garden clippings, fallen leaves, and biodegradable waste.",
        "កាកសំណល់អាហារ ស្លឹកឈើជ្រុះ កាកសំណល់សួនច្បារ និងសំណល់ងាយរលួយ។",
    ),
    (
        "Overflowing Bin",
        "ធុងសំរាមពេញហៀរ",
        "Public bins or community dumpsters that are full and spilling over.",
        "ធុងសំរាមសាធារណៈ ឬកន្លែងស្តុកសំរាមសហគមន៍ដែលពេញហៀរចេញក្រៅ។",
    ),
    (
        "Construction Debris",
        "សំណល់សំណង់",
        "Concrete chunks, bricks, wood scraps, tiles, and renovation rubble.",
        "កំទេចបេតុង ឥដ្ឋ ឈើសេសសល់ ក្បឿង និងសំណល់ពីការជួសជុលសំណង់។",
    ),
    (
        "Electronic Waste",
        "សំណល់អេឡិចត្រូនិក",
        "Broken appliances, batteries, cables, monitors, and e-waste.",
        "គ្រឿងអេឡិចត្រូនិកខូច ថ្មពិល ខ្សែភ្លើង ម៉ូនីទ័រ និងឧបករណ៍អគ្គិសនី។",
    ),
    (
        "Hazardous Waste",
        "សំណល់គ្រោះថ្នាក់",
        "Chemicals, paint cans, broken glass, oils, or medical waste.",
        "សារធាតុគីមី កំប៉ុងថ្នាំលាប កញ្ចក់បែក ប្រេងម៉ាស៊ីន ឬសំណល់វេជ្ជសាស្ត្រ។",
    ),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_columns(engine)
    db = SessionLocal()
    try:
        # 1. Seed Categories (bilingual EN + KM)
        category_map: dict[str, Category] = {}
        for name, name_km, desc, desc_km in DEFAULT_CATEGORIES:
            cat = db.scalar(select(Category).where(Category.name == name))
            if cat is None:
                cat = Category(
                    name=name,
                    name_km=name_km,
                    description=desc,
                    description_km=desc_km,
                )
                db.add(cat)
                db.flush()
            else:
                if not cat.name_km:
                    cat.name_km = name_km
                if not cat.description_km:
                    cat.description_km = desc_km
            category_map[name] = cat

        # 2. Seed Users
        admin = db.scalar(select(User).where(User.email == "admin@waste.local"))
        if admin is None:
            admin = User(
                full_name="System Administrator",
                email="admin@waste.local",
                password_hash=hash_password("Admin@123"),
                role="admin",
            )
            db.add(admin)
            db.flush()

        resident = db.scalar(select(User).where(User.email == "resident@waste.local"))
        if resident is None:
            resident = User(
                full_name="Dara Vann",
                email="resident@waste.local",
                password_hash=hash_password("Resident@123"),
                role="resident",
            )
            db.add(resident)
            db.flush()

        resident2 = db.scalar(select(User).where(User.email == "sokha@waste.local"))
        if resident2 is None:
            resident2 = User(
                full_name="Sokha Chan",
                email="sokha@waste.local",
                password_hash=hash_password("Resident@123"),
                role="resident",
            )
            db.add(resident2)
            db.flush()

        # 3. Seed Sample Reports only if database has no reports yet
        existing_reports = db.scalar(select(WasteReport.id).limit(1))
        if existing_reports is None:
            now = datetime.now(timezone.utc)

            sample_reports = [
                {
                    "user": resident,
                    "category": category_map["Overflowing Bin"],
                    "title": "Overflowing public trash bin near Central Market north gate",
                    "description": "The large green waste bin at the north entrance has been overflowing for two days, causing litter to scatter onto the sidewalk.",
                    "location_text": "Street 130, North Gate of Central Market, Daun Penh",
                    "latitude": 11.5696,
                    "longitude": 104.9210,
                    "status": "Resolved",
                    "days_ago": 6,
                    "history": [
                        (None, "Pending", resident, "Report submitted by resident.", 6),
                        ("Pending", "In Progress", admin, "Assigned to District Sanitation Team B.", 5),
                        ("In Progress", "Resolved", admin, "Bin emptied and surrounding sidewalk swept.", 4),
                    ],
                },
                {
                    "user": resident,
                    "category": category_map["Plastic Waste"],
                    "title": "Large pile of plastic bags dumped along canal walkway",
                    "description": "Multiple black bags filled with plastic bottles and foam food boxes were left near the drainage grate.",
                    "location_text": "Riverside Canal Path, near Bridge 2",
                    "latitude": 11.5564,
                    "longitude": 104.9282,
                    "status": "In Progress",
                    "days_ago": 3,
                    "history": [
                        (None, "Pending", resident, "Report submitted by resident.", 3),
                        ("Pending", "In Progress", admin, "Inspection completed; collection truck scheduled for tomorrow morning.", 2),
                    ],
                },
                {
                    "user": resident2,
                    "category": category_map["Construction Debris"],
                    "title": "Broken bricks and cement bags blocking pedestrian lane",
                    "description": "Leftover renovation debris was dumped overnight on the corner sidewalk, making it difficult to walk past.",
                    "location_text": "Street 271 & Street 371 Corner, Mean Chey",
                    "latitude": 11.5392,
                    "longitude": 104.9024,
                    "status": "Pending",
                    "days_ago": 1,
                    "history": [
                        (None, "Pending", resident2, "Report submitted by resident.", 1),
                    ],
                },
                {
                    "user": resident2,
                    "category": category_map["Organic Waste"],
                    "title": "Rotting fruit and vegetable crates behind local market",
                    "description": "Uncollected market organic waste producing strong odor and attracting flies near residential homes.",
                    "location_text": "Alleyway behind Orussey Market West Wing",
                    "latitude": 11.5618,
                    "longitude": 104.9165,
                    "status": "Resolved",
                    "days_ago": 8,
                    "history": [
                        (None, "Pending", resident2, "Report submitted by resident.", 8),
                        ("Pending", "In Progress", admin, "Market management notified and cleanup crew dispatched.", 7),
                        ("In Progress", "Resolved", admin, "Area cleared and washed down.", 6),
                    ],
                },
                {
                    "user": resident,
                    "category": category_map["Electronic Waste"],
                    "title": "Abandoned CRT monitors and tangled cables beside transformer",
                    "description": "Three broken computer monitors and damaged power supplies were left next to the electric pole.",
                    "location_text": "Toul Kork, Street 315 near Park Bench",
                    "latitude": 11.5761,
                    "longitude": 104.8975,
                    "status": "Pending",
                    "days_ago": 2,
                    "history": [
                        (None, "Pending", resident, "Report submitted by resident.", 2),
                    ],
                },
                {
                    "user": resident2,
                    "category": category_map["Plastic Waste"],
                    "title": "Scattered beverage cups after weekend community event",
                    "description": "Plastic cups and food wrappers accumulated near the south park benches and need sweeping.",
                    "location_text": "Botum Park South Lawn",
                    "latitude": 11.5593,
                    "longitude": 104.9311,
                    "status": "In Progress",
                    "days_ago": 2,
                    "history": [
                        (None, "Pending", resident2, "Report submitted by resident.", 2),
                        ("Pending", "In Progress", admin, "Park maintenance volunteers assigned for afternoon cleanup.", 1),
                    ],
                },
                {
                    "user": resident,
                    "category": category_map["Hazardous Waste"],
                    "title": "Open paint tins and broken fluorescent tubes in vacant lot",
                    "description": "Several partially filled paint cans and shattered glass tubes pose a safety hazard to neighborhood children.",
                    "location_text": "Sen Sok, Street 1986 Vacant Lot",
                    "latitude": 11.5844,
                    "longitude": 104.8812,
                    "status": "Pending",
                    "days_ago": 0,
                    "history": [
                        (None, "Pending", resident, "Report submitted by resident.", 0),
                    ],
                },
            ]

            for item in sample_reports:
                created_time = now - timedelta(days=item["days_ago"])
                report = WasteReport(
                    user_id=item["user"].id,
                    category_id=item["category"].id,
                    title=item["title"],
                    description=item["description"],
                    location_text=item["location_text"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    status=item["status"],
                    created_at=created_time,
                    updated_at=now - timedelta(days=item["history"][-1][4]),
                )
                db.add(report)
                db.flush()

                for old_st, new_st, actor, note, h_days in item["history"]:
                    db.add(
                        StatusHistory(
                            report_id=report.id,
                            changed_by=actor.id,
                            old_status=old_st,
                            new_status=new_st,
                            note=note,
                            changed_at=now - timedelta(days=h_days),
                        )
                    )

        db.commit()
        print("Database seeded successfully!")
        print("  Admin account:    admin@waste.local / Admin@123")
        print("  Resident account: resident@waste.local / Resident@123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
