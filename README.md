# MuleSpace - Campus Event Management Platform

A centralized event management and communication platform for campus departments, designed to streamline event coordination, reduce email spam, and automate attendance tracking.

## Features

- **Event Management**: Create, edit, and manage campus events
- **Shared Calendar**: View all campus events to avoid scheduling conflicts
- **Smart Notifications**: Targeted alerts based on department and interests
- **Automated Attendance**: QR code-based check-in system
- **Analytics Dashboard**: Event attendance tracking and reporting
- **Role-Based Access**: Student, Department Admin, and Admin roles

## Tech Stack

- **Backend**: Flask 3.0 with SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: Flask-Login with secure password hashing
- **Testing**: Pytest with 100% branch coverage
- **CI/CD**: GitHub Actions
- **Deployment**: Heroku with Gunicorn

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd MuleSpace

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run application
python run.py
```

## Project Status

- ✅ 149 tests passing
- ✅ 100% branch coverage
- ✅ Zero warnings
- ✅ Production ready
└── README.md                 # This file
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

MIT License

## Contact

For questions or support, contact Lisa Noble (Halloran Lab)
