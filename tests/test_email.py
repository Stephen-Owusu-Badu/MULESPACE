"""Tests for email functionality."""

import pytest
from unittest.mock import Mock, patch


class TestEmailFunctions:
    """Test email sending functions."""

    @patch('app.email.mail')
    def test_send_email_success(self, mock_mail, app):
        """Test successful email sending."""
        from app.email import send_email
        
        with app.app_context():
            send_email(
                subject="Test Subject",
                recipients=["test@example.com"],
                text_body="Test Body",
                html_body="<p>Test HTML</p>"
            )
            
            assert mock_mail.send.called

    @patch('app.email.mail')
    def test_send_email_with_sender(self, mock_mail, app):
        """Test email sending with custom sender."""
        from app.email import send_email
        
        with app.app_context():
            send_email(
                subject="Test Subject",
                recipients=["test@example.com"],
                text_body="Test Body",
                html_body="<p>Test HTML</p>",
                sender="custom@example.com"
            )
            
            assert mock_mail.send.called

    @patch('app.email.mail')
    def test_send_registration_confirmation(self, mock_mail, app, student_user, event):
        """Test sending registration confirmation email."""
        from app.email import send_registration_confirmation
        
        with app.app_context():
            send_registration_confirmation(student_user, event)
            assert mock_mail.send.called

    @patch('app.email.mail')
    def test_send_registration_confirmation_with_description(self, mock_mail, app, student_user, event):
        """Test confirmation email with event description."""
        from app.email import send_registration_confirmation
        
        with app.app_context():
            event.description = "Test event description"
            send_registration_confirmation(student_user, event)
            assert mock_mail.send.called

    @patch('app.email.mail')
    def test_send_email_multiple_recipients(self, mock_mail, app):
        """Test sending email to multiple recipients."""
        from app.email import send_email
        
        with app.app_context():
            recipients = ["test1@example.com", "test2@example.com"]
            send_email(
                subject="Test",
                recipients=recipients,
                text_body="Body",
                html_body="<p>HTML</p>"
            )
            assert mock_mail.send.called
