"""Email utility functions for MuleSpace."""
from flask import render_template_string
from flask_mail import Message
from app import mail


def send_email(subject, recipients, text_body, html_body, sender=None):
    """Send an email."""
    msg = Message(subject, recipients=recipients, sender=sender)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_registration_confirmation(user, event):
    """Send registration confirmation email to user."""
    subject = f"Confirmed: You're registered for {event.title}"
    
    # Plain text version
    text_body = f"""
Hi {user.first_name},

Great news! You've successfully registered for:

{event.title}

Event Details:
    Date: {event.start_time.strftime('%A, %B %d, %Y')}
    Time: {event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}
    Location: {event.location}
    Department: {event.department.name}

{event.description if event.description else ''}

We're excited to see you there! If you have any questions or need to make changes, 
please don't hesitate to reach out.

Best regards,
The MuleSpace Team
Colby College
"""

    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #003C71 0%, #6B9AC4 100%);
            color: white;
            padding: 30px;
            border-radius: 12px 12px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            background: white;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-top: none;
        }}
        .event-card {{
            background: #f8f9fa;
            border-left: 4px solid #003C71;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .event-title {{
            color: #003C71;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
        .detail-row {{
            padding: 8px 0;
            display: flex;
            align-items: flex-start;
        }}
        .detail-label {{
            font-weight: 500;
            color: #666;
            min-width: 100px;
        }}
        .detail-value {{
            color: #1a1a1a;
        }}
        .description {{
            background: white;
            padding: 16px;
            border-radius: 6px;
            margin-top: 16px;
            color: #666;
            line-height: 1.8;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-radius: 0 0 12px 12px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background: #003C71;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: 500;
        }}
        .message {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 16px;
            margin: 20px 0;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>✓ Registration Confirmed!</h1>
    </div>
    
    <div class="content">
        <p>Hi {user.first_name},</p>
        
        <p>Great news! You've successfully registered for the following event:</p>
        
        <div class="event-card">
            <div class="event-title">{event.title}</div>
            
            <div class="detail-row">
                <span class="detail-label">Date:</span>
                <span class="detail-value">{event.start_time.strftime('%A, %B %d, %Y')}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Time:</span>
                <span class="detail-value">{event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Location:</span>
                <span class="detail-value">{event.location}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">Department:</span>
                <span class="detail-value">{event.department.name}</span>
            </div>
            
            {f'<div class="description">{event.description}</div>' if event.description else ''}
        </div>
        
        <div class="message">
            <strong>📌 What's Next?</strong><br>
            We're excited to see you at this event! Make sure to add it to your calendar so you don't miss it. 
            When you arrive, you can check in using the QR code at the venue or through the MuleSpace app.
        </div>
        
        <p>If you have any questions or need to make changes to your registration, please don't hesitate to reach out to us.</p>
    </div>
    
    <div class="footer">
        <p><strong>MuleSpace</strong><br>
        Campus Event Management System<br>
        Colby College</p>
        <p style="font-size: 12px; color: #999;">
            This email was sent because you registered for an event through MuleSpace.
        </p>
    </div>
</body>
</html>
"""
    
    send_email(subject, [user.email], text_body, html_body)
