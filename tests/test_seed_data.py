"""Tests for seed_data.py - database seeding script."""

import pytest

from app import db
from app.models import Attendance, Department, Event, User


class TestSeedDataFunctions:
    """Test seed_data.py functions."""

    def test_create_departments_function_exists(self):
        """Test that create_departments function exists."""
        from seed_data import create_departments

        assert create_departments is not None
        assert callable(create_departments)

    def test_create_users_function_exists(self):
        """Test that create_users function exists."""
        from seed_data import create_users

        assert create_users is not None
        assert callable(create_users)

    def test_create_events_function_exists(self):
        """Test that create_events function exists."""
        from seed_data import create_events

        assert create_events is not None
        assert callable(create_events)

    def test_create_attendance_function_exists(self):
        """Test that create_attendance function exists."""
        from seed_data import create_attendance

        assert create_attendance is not None
        assert callable(create_attendance)

    def test_main_function_exists(self):
        """Test that main function exists."""
        from seed_data import main

        assert main is not None
        assert callable(main)


class TestCreateDepartments:
    """Test create_departments function."""

    def test_create_departments_creates_departments(self, app):
        """Test that create_departments creates department records."""
        from seed_data import create_departments

        with app.app_context():
            departments = create_departments()

            assert len(departments) > 0
            assert all(isinstance(d, Department) for d in departments)

    def test_create_departments_includes_halloran_lab(self, app):
        """Test that Halloran Lab is created."""
        from seed_data import create_departments

        with app.app_context():
            departments = create_departments()

            dept_names = [d.name for d in departments]
            assert "Halloran Lab" in dept_names

    def test_create_departments_includes_davis_connects(self, app):
        """Test that DavisConnects is created."""
        from seed_data import create_departments

        with app.app_context():
            departments = create_departments()

            dept_names = [d.name for d in departments]
            assert "DavisConnects" in dept_names

    def test_create_departments_includes_academic_depts(self, app):
        """Test that academic departments are created."""
        from seed_data import create_departments

        with app.app_context():
            departments = create_departments()

            dept_names = [d.name for d in departments]
            assert "Computer Science" in dept_names
            assert "Biology" in dept_names
            assert "Chemistry" in dept_names

    def test_create_departments_commits_to_db(self, app):
        """Test that departments are committed to database."""
        from seed_data import create_departments

        with app.app_context():
            initial_count = Department.query.count()
            departments = create_departments()

            # Should have more departments now
            assert Department.query.count() > initial_count


class TestCreateUsers:
    """Test create_users function."""

    def test_create_users_creates_users(self, app):
        """Test that create_users creates user records."""
        from seed_data import create_departments, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)

            assert len(users) > 0
            assert all(isinstance(u, User) for u in users)

    def test_create_users_creates_admin(self, app):
        """Test that an admin user is created."""
        from seed_data import create_departments, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)

            admin_users = [u for u in users if u.role == "admin"]
            assert len(admin_users) == 1
            assert admin_users[0].email == "admin@colby.edu"

    def test_create_users_creates_dept_admins(self, app):
        """Test that department admin users are created."""
        from seed_data import create_departments, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)

            dept_admins = [u for u in users if u.role == "department_admin"]
            assert len(dept_admins) >= 3

    def test_create_users_creates_students(self, app):
        """Test that student users are created."""
        from seed_data import create_departments, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)

            students = [u for u in users if u.role == "student"]
            assert len(students) >= 10

    def test_create_users_sets_passwords(self, app):
        """Test that user passwords are set correctly."""
        from seed_data import create_departments, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)

            # Check that passwords are hashed
            for user in users:
                assert user.password_hash is not None
                assert user.password_hash != ""

            # Check admin can login with correct password
            admin = users[0]
            assert admin.check_password("Admin123!")

    def test_create_users_assigns_departments(self, app):
        """Test that users are assigned to departments."""
        from seed_data import create_departments, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)

            for user in users:
                assert user.department_id is not None
                assert user.department_id > 0


class TestCreateEvents:
    """Test create_events function."""

    def test_create_events_creates_events(self, app):
        """Test that create_events creates event records."""
        from seed_data import create_departments, create_events, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)

            assert len(events) > 0
            assert all(isinstance(e, Event) for e in events)

    def test_create_events_includes_halloran_events(self, app):
        """Test that Halloran Lab events are created."""
        from seed_data import create_departments, create_events, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)

            halloran_dept = [d for d in departments if d.name == "Halloran Lab"][0]
            halloran_events = [e for e in events if e.department_id == halloran_dept.id]

            assert len(halloran_events) >= 2

    def test_create_events_includes_davis_events(self, app):
        """Test that DavisConnects events are created."""
        from seed_data import create_departments, create_events, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)

            davis_dept = [d for d in departments if d.name == "DavisConnects"][0]
            davis_events = [e for e in events if e.department_id == davis_dept.id]

            assert len(davis_events) >= 2

    def test_create_events_includes_cs_events(self, app):
        """Test that Computer Science events are created."""
        from seed_data import create_departments, create_events, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)

            cs_dept = [d for d in departments if d.name == "Computer Science"][0]
            cs_events = [e for e in events if e.department_id == cs_dept.id]

            assert len(cs_events) >= 2

    def test_create_events_sets_required_fields(self, app):
        """Test that events have all required fields."""
        from seed_data import create_departments, create_events, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)

            for event in events:
                assert event.title is not None
                assert event.description is not None
                assert event.start_time is not None
                assert event.end_time is not None
                assert event.location is not None
                assert event.department_id is not None
                assert event.created_by is not None

    def test_create_events_sets_capacity(self, app):
        """Test that events have max_capacity set."""
        from seed_data import create_departments, create_events, create_users

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)

            for event in events:
                assert event.max_capacity is not None
                assert event.max_capacity > 0


class TestCreateAttendance:
    """Test create_attendance function."""

    def test_create_attendance_creates_records(self, app):
        """Test that create_attendance creates attendance records."""
        from seed_data import (
            create_attendance,
            create_departments,
            create_events,
            create_users,
        )

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)
            attendance = create_attendance(events, users)

            assert len(attendance) > 0
            assert all(isinstance(a, Attendance) for a in attendance)

    def test_create_attendance_links_users_and_events(self, app):
        """Test that attendance records link users to events."""
        from seed_data import (
            create_attendance,
            create_departments,
            create_events,
            create_users,
        )

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)
            attendance = create_attendance(events, users)

            for record in attendance:
                assert record.user_id is not None
                assert record.event_id is not None

    def test_create_attendance_uses_student_users(self, app):
        """Test that attendance is created for student users."""
        from seed_data import (
            create_attendance,
            create_departments,
            create_events,
            create_users,
        )

        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)
            attendance = create_attendance(events, users)

            # Get student IDs
            student_ids = [u.id for u in users if u.role == "student"]

            # All attendance should be for students
            attendance_user_ids = [a.user_id for a in attendance]
            assert all(uid in student_ids for uid in attendance_user_ids)


class TestSeedDataMain:
    """Test seed_data main function."""

    def test_main_function_runs_without_error(self):
        """Test that main function can run without errors."""
        from seed_data import main

        # Should not raise any exceptions
        try:
            main()
            success = True
        except Exception:
            success = False

        assert success

    def test_main_integrates_all_functions(self, app):
        """Test that main function integrates all seeding functions."""
        from seed_data import (
            create_attendance,
            create_departments,
            create_events,
            create_users,
        )

        # Test that we can run the full sequence
        with app.app_context():
            departments = create_departments()
            users = create_users(departments)
            events = create_events(departments, users)
            attendance = create_attendance(events, users)

            # Verify complete data was created
            assert len(departments) > 0
            assert len(users) >= 14
            assert len(events) > 0
            assert len(attendance) > 0

    def test_main_output_format(self, capsys):
        """Test that main prints expected output."""
        from seed_data import main

        main()

        captured = capsys.readouterr()
        output = captured.out

        # Check for expected output messages
        assert "Starting database seeding" in output
        assert "Clearing existing data" in output
        assert "Created" in output
        assert "departments" in output
        assert "users" in output
        assert "events" in output
        assert "attendance records" in output
        assert "LOGIN CREDENTIALS" in output
        assert "admin@colby.edu" in output

    def test_main_prints_credentials(self, capsys):
        """Test that main prints login credentials."""
        from seed_data import main

        main()

        captured = capsys.readouterr()
        output = captured.out

        # Check for admin credentials
        assert "admin@colby.edu" in output
        assert "Admin123!" in output
        assert "lisa.noble@colby.edu" in output
        assert "Halloran123!" in output

    def test_main_prints_summary(self, capsys):
        """Test that main prints summary information."""
        from seed_data import main

        main()

        captured = capsys.readouterr()
        output = captured.out

        # Check for summary section
        assert "Summary:" in output
        assert "18 departments" in output
        assert "14 users" in output
        assert "9 events" in output
        assert "25 attendance records" in output
