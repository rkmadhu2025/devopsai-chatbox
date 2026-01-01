"""
Slack Integration Client
Send messages and interact with Slack
"""

import requests
from typing import Optional, Dict, List, Any
import json


class SlackClient:
    """Client for Slack API interactions."""

    def __init__(self, webhook_url: str = None, bot_token: str = None):
        """
        Initialize Slack client.

        Args:
            webhook_url: Incoming webhook URL for simple messaging
            bot_token: Bot token for full API access
        """
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.api_url = "https://slack.com/api"

        self.session = requests.Session()
        if bot_token:
            self.session.headers['Authorization'] = f'Bearer {bot_token}'
            self.session.headers['Content-Type'] = 'application/json; charset=utf-8'

    # Webhook Messages
    def send_webhook(self, text: str = None, blocks: List[Dict] = None,
                     attachments: List[Dict] = None) -> bool:
        """Send a message via webhook."""
        if not self.webhook_url:
            raise ValueError("Webhook URL not configured")

        payload = {}
        if text:
            payload['text'] = text
        if blocks:
            payload['blocks'] = blocks
        if attachments:
            payload['attachments'] = attachments

        response = requests.post(self.webhook_url, json=payload)
        return response.status_code == 200 and response.text == 'ok'

    # Bot API Messages
    def send_message(
        self,
        channel: str,
        text: str = None,
        blocks: List[Dict] = None,
        attachments: List[Dict] = None,
        thread_ts: str = None,
        unfurl_links: bool = True
    ) -> Dict:
        """Send a message via Bot API."""
        payload = {'channel': channel, 'unfurl_links': unfurl_links}
        if text:
            payload['text'] = text
        if blocks:
            payload['blocks'] = blocks
        if attachments:
            payload['attachments'] = attachments
        if thread_ts:
            payload['thread_ts'] = thread_ts

        response = self.session.post(f"{self.api_url}/chat.postMessage", json=payload)
        response.raise_for_status()
        return response.json()

    def update_message(
        self,
        channel: str,
        ts: str,
        text: str = None,
        blocks: List[Dict] = None
    ) -> Dict:
        """Update an existing message."""
        payload = {'channel': channel, 'ts': ts}
        if text:
            payload['text'] = text
        if blocks:
            payload['blocks'] = blocks

        response = self.session.post(f"{self.api_url}/chat.update", json=payload)
        response.raise_for_status()
        return response.json()

    def delete_message(self, channel: str, ts: str) -> Dict:
        """Delete a message."""
        payload = {'channel': channel, 'ts': ts}
        response = self.session.post(f"{self.api_url}/chat.delete", json=payload)
        response.raise_for_status()
        return response.json()

    # Channels
    def list_channels(self, types: str = "public_channel,private_channel") -> List[Dict]:
        """List channels."""
        response = self.session.get(
            f"{self.api_url}/conversations.list",
            params={'types': types, 'limit': 1000}
        )
        response.raise_for_status()
        return response.json().get('channels', [])

    def get_channel_info(self, channel: str) -> Dict:
        """Get channel information."""
        response = self.session.get(
            f"{self.api_url}/conversations.info",
            params={'channel': channel}
        )
        response.raise_for_status()
        return response.json().get('channel', {})

    # Users
    def list_users(self) -> List[Dict]:
        """List all users."""
        response = self.session.get(f"{self.api_url}/users.list")
        response.raise_for_status()
        return response.json().get('members', [])

    def get_user_info(self, user_id: str) -> Dict:
        """Get user information."""
        response = self.session.get(
            f"{self.api_url}/users.info",
            params={'user': user_id}
        )
        response.raise_for_status()
        return response.json().get('user', {})

    # Files
    def upload_file(
        self,
        channels: List[str],
        content: str = None,
        file_path: str = None,
        filename: str = None,
        title: str = None,
        initial_comment: str = None
    ) -> Dict:
        """Upload a file."""
        data = {'channels': ','.join(channels)}
        if title:
            data['title'] = title
        if initial_comment:
            data['initial_comment'] = initial_comment
        if filename:
            data['filename'] = filename

        files = None
        if file_path:
            files = {'file': open(file_path, 'rb')}
        elif content:
            data['content'] = content

        # Remove Content-Type for file upload
        headers = {'Authorization': f'Bearer {self.bot_token}'}

        response = requests.post(
            f"{self.api_url}/files.upload",
            data=data,
            files=files,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    # Block Kit Helpers
    @staticmethod
    def section_block(text: str, accessory: Dict = None) -> Dict:
        """Create a section block."""
        block = {
            'type': 'section',
            'text': {'type': 'mrkdwn', 'text': text}
        }
        if accessory:
            block['accessory'] = accessory
        return block

    @staticmethod
    def divider_block() -> Dict:
        """Create a divider block."""
        return {'type': 'divider'}

    @staticmethod
    def header_block(text: str) -> Dict:
        """Create a header block."""
        return {
            'type': 'header',
            'text': {'type': 'plain_text', 'text': text}
        }

    @staticmethod
    def context_block(elements: List[str]) -> Dict:
        """Create a context block."""
        return {
            'type': 'context',
            'elements': [{'type': 'mrkdwn', 'text': e} for e in elements]
        }

    @staticmethod
    def actions_block(elements: List[Dict]) -> Dict:
        """Create an actions block."""
        return {'type': 'actions', 'elements': elements}

    @staticmethod
    def button(text: str, action_id: str, value: str = None, style: str = None) -> Dict:
        """Create a button element."""
        button = {
            'type': 'button',
            'text': {'type': 'plain_text', 'text': text},
            'action_id': action_id
        }
        if value:
            button['value'] = value
        if style:
            button['style'] = style  # 'primary' or 'danger'
        return button

    # DevOps Notification Helpers
    def send_alert(
        self,
        channel: str,
        alert_name: str,
        severity: str,
        description: str,
        details: Dict = None,
        runbook_url: str = None
    ) -> Dict:
        """Send a formatted alert notification."""
        severity_emoji = {
            'critical': ':rotating_light:',
            'warning': ':warning:',
            'info': ':information_source:'
        }
        emoji = severity_emoji.get(severity.lower(), ':bell:')

        blocks = [
            self.header_block(f"{emoji} {severity.upper()}: {alert_name}"),
            self.section_block(description),
        ]

        if details:
            detail_text = '\n'.join([f"*{k}:* {v}" for k, v in details.items()])
            blocks.append(self.section_block(detail_text))

        if runbook_url:
            blocks.append(self.actions_block([
                self.button("View Runbook", "view_runbook", runbook_url, "primary")
            ]))

        return self.send_message(channel, blocks=blocks, text=f"{severity}: {alert_name}")

    def send_deployment(
        self,
        channel: str,
        app_name: str,
        version: str,
        environment: str,
        status: str,
        deploy_url: str = None,
        deployed_by: str = None
    ) -> Dict:
        """Send a deployment notification."""
        status_emoji = {
            'success': ':white_check_mark:',
            'failed': ':x:',
            'in_progress': ':hourglass:',
            'rollback': ':rewind:'
        }
        emoji = status_emoji.get(status.lower(), ':rocket:')

        blocks = [
            self.header_block(f"{emoji} Deployment {status.title()}"),
            self.section_block(
                f"*Application:* {app_name}\n"
                f"*Version:* {version}\n"
                f"*Environment:* {environment}\n"
                f"{f'*Deployed by:* {deployed_by}' if deployed_by else ''}"
            ),
        ]

        if deploy_url:
            blocks.append(self.actions_block([
                self.button("View Details", "view_deployment", deploy_url)
            ]))

        return self.send_message(channel, blocks=blocks, text=f"Deployment {status}: {app_name} {version}")

    def send_incident(
        self,
        channel: str,
        incident_id: str,
        title: str,
        severity: str,
        status: str,
        description: str = None,
        incident_url: str = None
    ) -> Dict:
        """Send an incident notification."""
        severity_color = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'warning',
            'low': 'good'
        }

        attachments = [{
            'color': severity_color.get(severity.lower(), '#808080'),
            'blocks': [
                self.header_block(f":fire: Incident {incident_id}: {title}"),
                self.section_block(
                    f"*Severity:* {severity}\n"
                    f"*Status:* {status}\n"
                    f"{description or ''}"
                )
            ]
        }]

        if incident_url:
            attachments[0]['blocks'].append(self.actions_block([
                self.button("View Incident", "view_incident", incident_url, "danger")
            ]))

        return self.send_message(channel, attachments=attachments, text=f"Incident {incident_id}: {title}")
