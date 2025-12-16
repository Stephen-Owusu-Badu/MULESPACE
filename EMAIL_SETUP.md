# Email Configuration Setup Guide

## Setting up Gmail for MuleSpace Email Notifications

Follow these steps to enable email notifications for event registrations:

### Step 1: Enable 2-Step Verification

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click on "2-Step Verification"
3. Follow the prompts to enable it (you'll need your phone)

### Step 2: Generate App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - If you don't see this option, make sure 2-Step Verification is enabled
2. Click "Select app" → Choose "Mail"
3. Click "Select device" → Choose "Other (Custom name)"
4. Type "MuleSpace" and click "Generate"
5. Google will show you a 16-character password - **COPY THIS!**

### Step 3: Configure MuleSpace

1. Create a `.env` file in the MuleSpace root directory (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your email credentials:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # The 16-char app password (spaces optional)
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

3. Save the file

### Step 4: Test the Email

1. Restart the Flask server
2. Log in as a student
3. Register for an event
4. Check your email inbox!

## Email Features

When a student registers for an event, they will receive:
- ✅ Confirmation email with event details
- 📅 Date, time, and location
- 📍 Full event description
- 🎨 Professional HTML formatting
- 📧 Plain text fallback for older email clients

## Troubleshooting

**Problem**: Emails not sending
- **Solution 1**: Check that your Gmail credentials are correct in `.env`
- **Solution 2**: Make sure 2-Step Verification is enabled
- **Solution 3**: Verify the app password is exactly as shown (16 characters)
- **Solution 4**: Check the Flask terminal for error messages

**Problem**: "Username and Password not accepted"
- **Solution**: You're using your regular Gmail password instead of the app password. Generate a new app password and use that instead.

**Problem**: Email goes to spam
- **Solution**: This is normal for development. In production, you'd want to use a professional email service like SendGrid or configure proper SPF/DKIM records.

## Alternative: Using Colby Email

If you want to use a Colby email address, you'll need:
1. SMTP server details from Colby IT
2. Update `MAIL_SERVER` in `.env` to Colby's SMTP server
3. Use your Colby email credentials

## Security Note

- ⚠️ Never commit the `.env` file to git (it's in `.gitignore`)
- ⚠️ The app password is specific to MuleSpace - you can revoke it anytime
- ⚠️ For production, consider using environment variables or a secrets manager
