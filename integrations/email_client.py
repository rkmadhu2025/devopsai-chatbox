"""
Email Client
Send emails via SMTP, SendGrid, or AWS SES
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, List, Any
import os


class EmailClient:
    """Client for sending emails via various providers."""

    def __init__(
        self,
        provider: str = "smtp",
        smtp_host: str = None,
        smtp_port: int = 587,
        smtp_username: str = None,
        smtp_password: str = None,
        smtp_use_tls: bool = True,
        sendgrid_api_key: str = None,
        ses_region: str = None,
        default_from: str = None
    ):
        """
        Initialize Email client.

        Args:
            provider: Email provider ("smtp", "sendgrid", "ses")
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            smtp_use_tls: Use TLS for SMTP
            sendgrid_api_key: SendGrid API key
            ses_region: AWS SES region
            default_from: Default from address
        """
        self.provider = provider.lower()
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.sendgrid_api_key = sendgrid_api_key
        self.ses_region = ses_region
        self.default_from = default_from

    def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        from_email: str = None,
        html: bool = False,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict] = None,
        reply_to: str = None
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            from_email: From address (uses default if not provided)
            html: True if body is HTML
            cc: List of CC addresses
            bcc: List of BCC addresses
            attachments: List of {"filename": str, "content": bytes, "mime_type": str}
            reply_to: Reply-to address

        Returns:
            Result dict with status
        """
        from_email = from_email or self.default_from

        if self.provider == "smtp":
            return self._send_smtp(to, subject, body, from_email, html, cc, bcc, attachments, reply_to)
        elif self.provider == "sendgrid":
            return self._send_sendgrid(to, subject, body, from_email, html, cc, bcc, attachments, reply_to)
        elif self.provider == "ses":
            return self._send_ses(to, subject, body, from_email, html, cc, bcc, attachments, reply_to)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _send_smtp(
        self, to, subject, body, from_email, html, cc, bcc, attachments, reply_to
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ', '.join(to)

        if cc:
            msg['Cc'] = ', '.join(cc)
        if reply_to:
            msg['Reply-To'] = reply_to

        # Attach body
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Attach files
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f"attachment; filename={attachment['filename']}"
                )
                msg.attach(part)

        # All recipients
        all_recipients = to + (cc or []) + (bcc or [])

        try:
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.sendmail(from_email, all_recipients, msg.as_string())
            server.quit()

            return {'status': 'success', 'message': 'Email sent successfully'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _send_sendgrid(
        self, to, subject, body, from_email, html, cc, bcc, attachments, reply_to
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        try:
            import sendgrid
            from sendgrid.helpers.mail import (
                Mail, Email, To, Content, Attachment, FileContent,
                FileName, FileType, Disposition, Cc, Bcc, ReplyTo
            )
        except ImportError:
            return {'status': 'error', 'message': 'sendgrid package not installed'}

        sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)

        message = Mail(
            from_email=Email(from_email),
            to_emails=[To(email) for email in to],
            subject=subject,
            html_content=Content("text/html", body) if html else None,
            plain_text_content=Content("text/plain", body) if not html else None
        )

        if cc:
            for email in cc:
                message.add_cc(Cc(email))

        if bcc:
            for email in bcc:
                message.add_bcc(Bcc(email))

        if reply_to:
            message.reply_to = ReplyTo(reply_to)

        if attachments:
            import base64
            for attachment in attachments:
                attached_file = Attachment(
                    FileContent(base64.b64encode(attachment['content']).decode()),
                    FileName(attachment['filename']),
                    FileType(attachment.get('mime_type', 'application/octet-stream')),
                    Disposition('attachment')
                )
                message.add_attachment(attached_file)

        try:
            response = sg.send(message)
            return {
                'status': 'success',
                'message': 'Email sent successfully',
                'status_code': response.status_code
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _send_ses(
        self, to, subject, body, from_email, html, cc, bcc, attachments, reply_to
    ) -> Dict[str, Any]:
        """Send email via AWS SES."""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            return {'status': 'error', 'message': 'boto3 package not installed'}

        client = boto3.client('ses', region_name=self.ses_region)

        destination = {'ToAddresses': to}
        if cc:
            destination['CcAddresses'] = cc
        if bcc:
            destination['BccAddresses'] = bcc

        message = {
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {}
        }

        if html:
            message['Body']['Html'] = {'Data': body, 'Charset': 'UTF-8'}
        else:
            message['Body']['Text'] = {'Data': body, 'Charset': 'UTF-8'}

        try:
            kwargs = {
                'Source': from_email,
                'Destination': destination,
                'Message': message
            }
            if reply_to:
                kwargs['ReplyToAddresses'] = [reply_to]

            response = client.send_email(**kwargs)
            return {
                'status': 'success',
                'message': 'Email sent successfully',
                'message_id': response['MessageId']
            }
        except ClientError as e:
            return {'status': 'error', 'message': str(e)}

    # Template helpers
    def send_alert(
        self,
        to: List[str],
        alert_name: str,
        severity: str,
        description: str,
        details: Dict = None,
        from_email: str = None
    ) -> Dict[str, Any]:
        """Send a formatted alert email."""
        severity_colors = {
            'critical': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }
        color = severity_colors.get(severity.lower(), '#6c757d')

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">{severity.upper()} ALERT</h1>
            </div>
            <div style="padding: 20px;">
                <h2>{alert_name}</h2>
                <p>{description}</p>
                {'<h3>Details:</h3><pre>' + str(details) + '</pre>' if details else ''}
            </div>
        </body>
        </html>
        """

        return self.send(
            to=to,
            subject=f"[{severity.upper()}] {alert_name}",
            body=html_body,
            html=True,
            from_email=from_email
        )

    def send_deployment_notification(
        self,
        to: List[str],
        app_name: str,
        version: str,
        environment: str,
        status: str,
        deploy_url: str = None,
        from_email: str = None
    ) -> Dict[str, Any]:
        """Send a deployment notification email."""
        status_colors = {
            'success': '#28a745',
            'failed': '#dc3545',
            'in_progress': '#ffc107'
        }
        color = status_colors.get(status.lower(), '#6c757d')

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">Deployment {status.upper()}</h1>
            </div>
            <div style="padding: 20px;">
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Application</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{app_name}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Version</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{version}</td></tr>
                    <tr><td style="padding: 10px; border: 1px solid #ddd;"><strong>Environment</strong></td><td style="padding: 10px; border: 1px solid #ddd;">{environment}</td></tr>
                </table>
                {f'<p><a href="{deploy_url}">View Deployment</a></p>' if deploy_url else ''}
            </div>
        </body>
        </html>
        """

        return self.send(
            to=to,
            subject=f"[{environment.upper()}] {app_name} v{version} - Deployment {status}",
            body=html_body,
            html=True,
            from_email=from_email
        )
