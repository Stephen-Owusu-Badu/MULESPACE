from datetime import datetime, timedelta

import pytest

from app import create_app, db
from app.models import Department, Event, User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def department(app):
    """Create a test department."""
    dept = Department(name="Computer Science", description="CS Department")
    db.session.add(dept)
    db.session.commit()
    return dept


@pytest.fixture
def student_user(app, department):
    """Create a test student user."""
    user = User(
        email="student@test.com",
        username="student",
        first_name="Test",
        last_name="Student",
        role="student",
        department_id=department.id,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app, department):
    """Create a test admin user."""
    user = User(
        email="admin@test.com",
        username="admin",
        first_name="Test",
        last_name="Admin",
        role="admin",
        department_id=department.id,
    )
    user.set_password("admin123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def dept_admin_user(app, department):
    """Create a test department admin user."""
    user = User(
        email="deptadmin@test.com",
        username="deptadmin",
        first_name="Dept",
        last_name="Admin",
        role="department_admin",
        department_id=department.id,
    )
    user.set_password("deptadmin123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def event(app, department, admin_user):
    """Create a test event."""
    event = Event(
        title="Test Event",
        description="Test Description",
        location="Test Location",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=2),
        max_capacity=50,
        department_id=department.id,
        created_by=admin_user.id,
    )
    db.session.add(event)
    db.session.commit()
    return event


@pytest.fixture
def authenticated_client(client, student_user):
    """Create authenticated client."""
    with client:
        client.post(
            "/api/auth/login",
            json={"email": "student@test.com", "password": "password123"},
        )
        yield client


@pytest.fixture
def admin_client(client, admin_user):
    """Create authenticated admin client."""
    with client:
        client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "admin123"},
        )
        yield client


@pytest.fixture
def dept_admin_client(client, dept_admin_user):
    """Create authenticated department admin client."""
    with client:
        client.post(
            "/api/auth/login",
            json={"email": "deptadmin@test.com", "password": "deptadmin123"},
        )
        yield client
