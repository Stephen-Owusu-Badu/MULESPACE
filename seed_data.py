"""Seed data script for MuleSpace - Colby College.

This script populates the database with initial data including:
- Departments (Halloran Lab, DavisConnects, and academic departments)
- Admin and department admin users
- Student users
- Sample events
- Some attendance records
"""

from datetime import datetime, timedelta

from app import create_app, db
from app.models import Attendance, Department, Event, Notification, User


def create_departments():
    """Create Colby College departments."""
    departments = [
        "Halloran Lab",
        "DavisConnects",
        "Computer Science",
        "Biology",
        "Chemistry",
        "Mathematics",
        "English",
        "History",
        "Psychology",
        "Economics",
        "Environmental Studies",
        "Art",
        "Music",
        "Theater and Dance",
        "Physics",
        "Philosophy",
        "Government",
        "Anthropology",
    ]

    dept_objects = []
    for dept_name in departments:
        dept = Department(name=dept_name)
        db.session.add(dept)
        dept_objects.append(dept)

    db.session.commit()
    print(f"✅ Created {len(dept_objects)} departments")
    return dept_objects


def create_users(departments):
    """Create admin, department admins, and students."""
    users = []

    # System Admin
    admin = User(
        email="admin@colby.edu",
        username="admin",
        first_name="System",
        last_name="Administrator",
        role="admin",
        department_id=departments[0].id,  # Halloran Lab
        is_active=True,
    )
    admin.set_password("Admin123!")
    db.session.add(admin)
    users.append(admin)

    # Halloran Lab Director (Department Admin)
    halloran_admin = User(
        email="lisa.noble@colby.edu",
        username="lnoble",
        first_name="Lisa",
        last_name="Noble",
        role="department_admin",
        department_id=departments[0].id,  # Halloran Lab
        is_active=True,
    )
    halloran_admin.set_password("Halloran123!")
    db.session.add(halloran_admin)
    users.append(halloran_admin)

    # DavisConnects Coordinator (Department Admin)
    davis_admin = User(
        email="coordinator@davisconnects.colby.edu",
        username="dconnects",
        first_name="Davis",
        last_name="Coordinator",
        role="department_admin",
        department_id=departments[1].id,  # DavisConnects
        is_active=True,
    )
    davis_admin.set_password("Davis123!")
    db.session.add(davis_admin)
    users.append(davis_admin)

    # CS Department Admin
    cs_admin = User(
        email="cs.admin@colby.edu",
        username="csadmin",
        first_name="Computer Science",
        last_name="Admin",
        role="department_admin",
        department_id=departments[2].id,  # Computer Science
        is_active=True,
    )
    cs_admin.set_password("CS123!")
    db.session.add(cs_admin)
    users.append(cs_admin)

    # Student users
    student_data = [
        ("john.smith@colby.edu", "jsmith", "John", "Smith", 2),  # CS
        ("emma.johnson@colby.edu", "ejohnson", "Emma", "Johnson", 3),  # Biology
        ("michael.brown@colby.edu", "mbrown", "Michael", "Brown", 2),  # CS
        ("sarah.davis@colby.edu", "sdavis", "Sarah", "Davis", 4),  # Chemistry
        ("james.wilson@colby.edu", "jwilson", "James", "Wilson", 5),  # Mathematics
        ("olivia.taylor@colby.edu", "otaylor", "Olivia", "Taylor", 6),  # English
        ("william.anderson@colby.edu", "wanderson", "William", "Anderson", 7),  # History
        (
            "sophia.martinez@colby.edu",
            "smartinez",
            "Sophia",
            "Martinez",
            8,
        ),  # Psychology
        ("alexander.garcia@colby.edu", "agarcia", "Alexander", "Garcia", 9),  # Economics
        (
            "isabella.rodriguez@colby.edu",
            "irodriguez",
            "Isabella",
            "Rodriguez",
            10,
        ),  # Environmental Studies
        ("sowusu27@colby.edu", "sowusu27", "Stephen", "Owusu Badu", 2),  # CS
    ]

    for email, username, first_name, last_name, dept_idx in student_data:
        student = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role="student",
            department_id=departments[dept_idx].id,
            is_active=True,
        )
        student.set_password("StudentColby!")
        db.session.add(student)
        users.append(student)

    db.session.commit()
    print(f" Created {len(users)} users (1 admin, 3 dept admins, 11 students)")
    return users


def create_events(departments, users):
    """Create sample events."""
    # Get the admin and dept admins
    admin = users[0]
    halloran_admin = users[1]
    davis_admin = users[2]
    cs_admin = users[3]

    events = []

    # Halloran Lab Events
    halloran_events = [
        {
            "title": "Research Symposium 2025",
            "description": "Annual undergraduate research symposium showcasing student projects across all disciplines",
            "start_time": datetime(2025, 12, 18, 14, 0),
            "end_time": datetime(2025, 12, 18, 17, 0),
            "location": "Diamond Building, Main Hall",
            "max_capacity": 200,
            "department_id": departments[0].id,
            "created_by": halloran_admin.id,
        },
        {
            "title": "Science Lecture Series: Climate Change",
            "description": "Guest speaker Dr. Jane Miller discusses climate change impacts in Maine",
            "start_time": datetime(2025, 12, 20, 18, 0),
            "end_time": datetime(2025, 12, 20, 19, 30),
            "location": "Olin Science Center, Room 101",
            "max_capacity": 100,
            "department_id": departments[0].id,
            "created_by": halloran_admin.id,
        },
    ]

    # DavisConnects Events
    davis_events = [
        {
            "title": "Career Fair: Spring 2026",
            "description": "Connect with employers and explore internship and job opportunities",
            "start_time": datetime(2025, 12, 19, 10, 0),
            "end_time": datetime(2025, 12, 19, 15, 0),
            "location": "Cotter Union, Main Lounge",
            "max_capacity": 500,
            "department_id": departments[1].id,
            "created_by": davis_admin.id,
        },
        {
            "title": "Resume Workshop",
            "description": "Learn how to craft an effective resume and cover letter",
            "start_time": datetime(2025, 12, 21, 16, 0),
            "end_time": datetime(2025, 12, 21, 17, 30),
            "location": "Career Center",
            "max_capacity": 30,
            "department_id": departments[1].id,
            "created_by": davis_admin.id,
        },
    ]

    # Computer Science Events
    cs_events = [
        {
            "title": "Introduction to Machine Learning",
            "description": "Workshop on ML fundamentals using Python and scikit-learn",
            "start_time": datetime(2025, 12, 22, 13, 0),
            "end_time": datetime(2025, 12, 22, 15, 0),
            "location": "Davis Science Center, Room 205",
            "max_capacity": 40,
            "department_id": departments[2].id,
            "created_by": cs_admin.id,
        },
        {
            "title": "Hackathon 2025",
            "description": "24-hour coding challenge with prizes and free food!",
            "start_time": datetime(2025, 12, 27, 18, 0),
            "end_time": datetime(2025, 12, 28, 18, 0),
            "location": "Diamond Building, Tech Commons",
            "max_capacity": 80,
            "department_id": departments[2].id,
            "created_by": cs_admin.id,
        },
    ]

    # Biology Department Event
    bio_events = [
        {
            "title": "Field Trip: Bigelow Laboratory",
            "description": "Visit to Bigelow Laboratory for Ocean Sciences in Boothbay Harbor",
            "start_time": datetime(2025, 12, 23, 9, 0),
            "end_time": datetime(2025, 12, 23, 16, 0),
            "location": "Meet at Olin Science Center",
            "max_capacity": 25,
            "department_id": departments[3].id,
            "created_by": admin.id,
        }
    ]

    # Academic Events
    academic_events = [
        {
            "title": "Poetry Reading: Local Authors",
            "description": "Evening of poetry readings by Maine authors",
            "start_time": datetime(2025, 12, 19, 19, 0),
            "end_time": datetime(2025, 12, 19, 21, 0),
            "location": "Miller Library, Special Collections",
            "max_capacity": 50,
            "department_id": departments[6].id,  # English
            "created_by": admin.id,
        },
        {
            "title": "Study Abroad Info Session",
            "description": "Learn about study abroad opportunities for next academic year",
            "start_time": datetime(2025, 12, 20, 12, 0),
            "end_time": datetime(2025, 12, 20, 13, 0),
            "location": "Cotter Union, Room 215",
            "max_capacity": 60,
            "department_id": departments[1].id,  # DavisConnects
            "created_by": davis_admin.id,
        },
    ]

    all_events = (
        halloran_events + davis_events + cs_events + bio_events + academic_events
    )

    for event_data in all_events:
        event = Event(**event_data)
        db.session.add(event)
        events.append(event)

    db.session.commit()
    print(f"✅ Created {len(events)} events")
    return events


def create_attendance(events, users):
    """Create sample attendance records."""
    # Students are users[4:14]
    students = users[4:14]
    attendance_records = []

    # First event - Research Symposium (many attendees)
    for student in students[:8]:
        attendance = Attendance(event_id=events[0].id, user_id=student.id)
        db.session.add(attendance)
        attendance_records.append(attendance)

    # Career Fair (most students)
    for student in students:
        attendance = Attendance(event_id=events[2].id, user_id=student.id)
        db.session.add(attendance)
        attendance_records.append(attendance)

    # ML Workshop (CS students)
    for student in students[:4]:
        attendance = Attendance(event_id=events[4].id, user_id=student.id)
        db.session.add(attendance)
        attendance_records.append(attendance)

    # Poetry Reading (few students)
    for student in students[5:8]:
        attendance = Attendance(event_id=events[7].id, user_id=student.id)
        db.session.add(attendance)
        attendance_records.append(attendance)

    db.session.commit()
    print(f"✅ Created {len(attendance_records)} attendance records")
    return attendance_records


def main():
    """Run the seed data script."""
    app = create_app("development")

    with app.app_context():
        print("🌱 Starting database seeding...")

        # Clear existing data
        print("🗑️  Clearing existing data...")
        Notification.query.delete()
        Attendance.query.delete()
        Event.query.delete()
        User.query.delete()
        Department.query.delete()
        db.session.commit()

        # Create new data
        departments = create_departments()
        users = create_users(departments)
        events = create_events(departments, users)
        attendance = create_attendance(events, users)

        print("\n✅ Database seeding completed successfully!\n")
        print("=" * 60)
        print("LOGIN CREDENTIALS:")
        print("=" * 60)
        print("\n🔑 System Admin:")
        print("   Email: admin@colby.edu")
        print("   Password: Admin123!")
        print("\n🔑 Halloran Lab Director:")
        print("   Email: lisa.noble@colby.edu")
        print("   Password: Halloran123!")
        print("\n🔑 DavisConnects Coordinator:")
        print("   Email: coordinator@davisconnects.colby.edu")
        print("   Password: Davis123!")
        print("\n🔑 CS Department Admin:")
        print("   Email: cs.admin@colby.edu")
        print("   Password: CS123!")
        print("\n👤 Sample Student:")
        print("   Email: john.smith@colby.edu")
        print("   Password: Student123!")
        print("\n" + "=" * 60)
        print(f"📊 Summary:")
        print(f"   - {len(departments)} departments")
        print(f"   - {len(users)} users (1 admin, 3 dept admins, 10 students)")
        print(f"   - {len(events)} events")
        print(f"   - {len(attendance)} attendance records")
        print("=" * 60)


if __name__ == "__main__":
    main()
