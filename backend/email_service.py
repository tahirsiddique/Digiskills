"""Email notification service."""
import asyncio
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from config import settings


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        self.enabled = settings.SMTP_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email."""
        if not self.enabled:
            print(f"Email not sent (SMTP disabled): {subject} to {to_email}")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject

            # Add plain text part
            message.attach(MIMEText(body, "plain"))

            # Add HTML part if provided
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            print(f"Email sent successfully: {subject} to {to_email}")
            return True

        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    def _get_ticket_url(self, ticket_id: int) -> str:
        """Get the URL for a ticket."""
        # This should be configured based on your frontend URL
        return f"http://localhost/tickets/{ticket_id}"

    async def send_ticket_created_notification(
        self,
        ticket_number: str,
        ticket_id: int,
        title: str,
        creator_email: str,
        creator_name: str
    ):
        """Notify user that their ticket was created."""
        subject = f"Ticket Created: {ticket_number}"

        body = f"""
Hello {creator_name},

Your support ticket has been created successfully.

Ticket Number: {ticket_number}
Title: {title}

You can track your ticket status at: {self._get_ticket_url(ticket_id)}

Our support team will respond to your ticket shortly.

Best regards,
Digiskills Support Team
        """

        html_body = f"""
<html>
<body>
    <h2>Ticket Created Successfully</h2>
    <p>Hello {creator_name},</p>
    <p>Your support ticket has been created successfully.</p>

    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 8px; font-weight: bold;">Ticket Number:</td>
            <td style="padding: 8px;">{ticket_number}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Title:</td>
            <td style="padding: 8px;">{title}</td>
        </tr>
    </table>

    <p>
        <a href="{self._get_ticket_url(ticket_id)}"
           style="background-color: #2563eb; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            View Ticket
        </a>
    </p>

    <p>Our support team will respond to your ticket shortly.</p>

    <p>Best regards,<br>Digiskills Support Team</p>
</body>
</html>
        """

        await self.send_email(creator_email, subject, body, html_body)

    async def send_ticket_assigned_notification(
        self,
        ticket_number: str,
        ticket_id: int,
        title: str,
        assignee_email: str,
        assignee_name: str,
        priority: str
    ):
        """Notify technician that a ticket was assigned to them."""
        subject = f"Ticket Assigned: {ticket_number} - {title}"

        body = f"""
Hello {assignee_name},

A support ticket has been assigned to you.

Ticket Number: {ticket_number}
Title: {title}
Priority: {priority.upper()}

Please review and respond to this ticket: {self._get_ticket_url(ticket_id)}

Best regards,
Digiskills Support Team
        """

        html_body = f"""
<html>
<body>
    <h2>New Ticket Assigned</h2>
    <p>Hello {assignee_name},</p>
    <p>A support ticket has been assigned to you.</p>

    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 8px; font-weight: bold;">Ticket Number:</td>
            <td style="padding: 8px;">{ticket_number}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Title:</td>
            <td style="padding: 8px;">{title}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Priority:</td>
            <td style="padding: 8px;">
                <span style="background-color: {'#fecaca' if priority == 'critical' else '#fed7aa' if priority == 'high' else '#fef3c7'};
                             padding: 4px 12px; border-radius: 12px; font-weight: 500;">
                    {priority.upper()}
                </span>
            </td>
        </tr>
    </table>

    <p>
        <a href="{self._get_ticket_url(ticket_id)}"
           style="background-color: #2563eb; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            View Ticket
        </a>
    </p>

    <p>Best regards,<br>Digiskills Support Team</p>
</body>
</html>
        """

        await self.send_email(assignee_email, subject, body, html_body)

    async def send_ticket_status_changed_notification(
        self,
        ticket_number: str,
        ticket_id: int,
        title: str,
        old_status: str,
        new_status: str,
        user_email: str,
        user_name: str
    ):
        """Notify user of ticket status change."""
        subject = f"Ticket Status Updated: {ticket_number}"

        body = f"""
Hello {user_name},

The status of your support ticket has been updated.

Ticket Number: {ticket_number}
Title: {title}
Previous Status: {old_status.replace('_', ' ').title()}
New Status: {new_status.replace('_', ' ').title()}

View your ticket: {self._get_ticket_url(ticket_id)}

Best regards,
Digiskills Support Team
        """

        html_body = f"""
<html>
<body>
    <h2>Ticket Status Updated</h2>
    <p>Hello {user_name},</p>
    <p>The status of your support ticket has been updated.</p>

    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 8px; font-weight: bold;">Ticket Number:</td>
            <td style="padding: 8px;">{ticket_number}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Title:</td>
            <td style="padding: 8px;">{title}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Previous Status:</td>
            <td style="padding: 8px;">{old_status.replace('_', ' ').title()}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">New Status:</td>
            <td style="padding: 8px;">
                <span style="background-color: {'#d1fae5' if new_status == 'resolved' else '#fef3c7'};
                             padding: 4px 12px; border-radius: 12px; font-weight: 500;">
                    {new_status.replace('_', ' ').title()}
                </span>
            </td>
        </tr>
    </table>

    <p>
        <a href="{self._get_ticket_url(ticket_id)}"
           style="background-color: #2563eb; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            View Ticket
        </a>
    </p>

    <p>Best regards,<br>Digiskills Support Team</p>
</body>
</html>
        """

        await self.send_email(user_email, subject, body, html_body)

    async def send_new_comment_notification(
        self,
        ticket_number: str,
        ticket_id: int,
        title: str,
        commenter_name: str,
        comment_text: str,
        recipient_email: str,
        recipient_name: str
    ):
        """Notify user of new comment on their ticket."""
        subject = f"New Comment on Ticket: {ticket_number}"

        body = f"""
Hello {recipient_name},

A new comment has been added to your support ticket.

Ticket Number: {ticket_number}
Title: {title}
Comment by: {commenter_name}

Comment:
{comment_text[:200]}{'...' if len(comment_text) > 200 else ''}

View full ticket: {self._get_ticket_url(ticket_id)}

Best regards,
Digiskills Support Team
        """

        html_body = f"""
<html>
<body>
    <h2>New Comment on Ticket</h2>
    <p>Hello {recipient_name},</p>
    <p>A new comment has been added to your support ticket.</p>

    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 8px; font-weight: bold;">Ticket Number:</td>
            <td style="padding: 8px;">{ticket_number}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Title:</td>
            <td style="padding: 8px;">{title}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Comment by:</td>
            <td style="padding: 8px;">{commenter_name}</td>
        </tr>
    </table>

    <div style="background-color: #f8fafc; padding: 15px; border-left: 4px solid #2563eb; margin: 20px 0;">
        <p style="margin: 0;">{comment_text[:300]}{'...' if len(comment_text) > 300 else ''}</p>
    </div>

    <p>
        <a href="{self._get_ticket_url(ticket_id)}"
           style="background-color: #2563eb; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 5px; display: inline-block;">
            View Full Ticket
        </a>
    </p>

    <p>Best regards,<br>Digiskills Support Team</p>
</body>
</html>
        """

        await self.send_email(recipient_email, subject, body, html_body)


# Global email service instance
email_service = EmailService()
