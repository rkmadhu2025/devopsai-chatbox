"""
PagerDuty Integration Client
Create and manage incidents via PagerDuty Events API
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import json


class PagerDutyClient:
    """Client for PagerDuty API interactions."""

    def __init__(
        self,
        api_key: str = None,
        integration_key: str = None,
        default_from_email: str = None
    ):
        """
        Initialize PagerDuty client.

        Args:
            api_key: PagerDuty REST API key for full API access
            integration_key: Events API v2 integration key for sending events
            default_from_email: Default email for API operations
        """
        self.api_key = api_key
        self.integration_key = integration_key
        self.default_from_email = default_from_email
        self.api_url = "https://api.pagerduty.com"
        self.events_url = "https://events.pagerduty.com/v2/enqueue"

        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Token token={api_key}'
            self.session.headers['Content-Type'] = 'application/json'

    # Events API v2
    def trigger_event(
        self,
        summary: str,
        severity: str = "error",
        source: str = "devops-chatbot",
        dedup_key: str = None,
        custom_details: Dict = None,
        links: List[Dict] = None,
        images: List[Dict] = None,
        routing_key: str = None
    ) -> Dict:
        """
        Trigger an alert event.

        Args:
            summary: Alert summary (max 1024 chars)
            severity: Severity level (critical, error, warning, info)
            source: Source of the event
            dedup_key: Deduplication key
            custom_details: Additional details
            links: List of {"href": url, "text": label}
            images: List of {"src": url, "href": link, "alt": alt_text}
            routing_key: Override integration key

        Returns:
            Event response with dedup_key
        """
        payload = {
            "routing_key": routing_key or self.integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary[:1024],
                "severity": severity.lower(),
                "source": source,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

        if dedup_key:
            payload["dedup_key"] = dedup_key
        if custom_details:
            payload["payload"]["custom_details"] = custom_details
        if links:
            payload["links"] = links
        if images:
            payload["images"] = images

        response = requests.post(self.events_url, json=payload)
        response.raise_for_status()
        return response.json()

    def acknowledge_event(self, dedup_key: str, routing_key: str = None) -> Dict:
        """Acknowledge an existing alert."""
        payload = {
            "routing_key": routing_key or self.integration_key,
            "event_action": "acknowledge",
            "dedup_key": dedup_key
        }

        response = requests.post(self.events_url, json=payload)
        response.raise_for_status()
        return response.json()

    def resolve_event(self, dedup_key: str, routing_key: str = None) -> Dict:
        """Resolve an existing alert."""
        payload = {
            "routing_key": routing_key or self.integration_key,
            "event_action": "resolve",
            "dedup_key": dedup_key
        }

        response = requests.post(self.events_url, json=payload)
        response.raise_for_status()
        return response.json()

    # REST API - Incidents
    def list_incidents(
        self,
        statuses: List[str] = None,
        urgencies: List[str] = None,
        service_ids: List[str] = None,
        since: str = None,
        until: str = None,
        limit: int = 25
    ) -> List[Dict]:
        """List incidents."""
        params = {'limit': limit}
        if statuses:
            params['statuses[]'] = statuses
        if urgencies:
            params['urgencies[]'] = urgencies
        if service_ids:
            params['service_ids[]'] = service_ids
        if since:
            params['since'] = since
        if until:
            params['until'] = until

        response = self.session.get(f"{self.api_url}/incidents", params=params)
        response.raise_for_status()
        return response.json().get('incidents', [])

    def get_incident(self, incident_id: str) -> Dict:
        """Get incident details."""
        response = self.session.get(f"{self.api_url}/incidents/{incident_id}")
        response.raise_for_status()
        return response.json().get('incident', {})

    def create_incident(
        self,
        title: str,
        service_id: str,
        urgency: str = "high",
        body: str = None,
        escalation_policy_id: str = None,
        from_email: str = None
    ) -> Dict:
        """Create a new incident via REST API."""
        incident = {
            "type": "incident",
            "title": title,
            "service": {"id": service_id, "type": "service_reference"},
            "urgency": urgency
        }

        if body:
            incident["body"] = {"type": "incident_body", "details": body}
        if escalation_policy_id:
            incident["escalation_policy"] = {
                "id": escalation_policy_id,
                "type": "escalation_policy_reference"
            }

        headers = {'From': from_email or self.default_from_email}

        response = self.session.post(
            f"{self.api_url}/incidents",
            json={"incident": incident},
            headers=headers
        )
        response.raise_for_status()
        return response.json().get('incident', {})

    def update_incident(
        self,
        incident_id: str,
        status: str = None,
        resolution: str = None,
        title: str = None,
        urgency: str = None,
        from_email: str = None
    ) -> Dict:
        """Update an incident."""
        incident = {"id": incident_id, "type": "incident"}
        if status:
            incident["status"] = status
        if resolution:
            incident["resolution"] = resolution
        if title:
            incident["title"] = title
        if urgency:
            incident["urgency"] = urgency

        headers = {'From': from_email or self.default_from_email}

        response = self.session.put(
            f"{self.api_url}/incidents/{incident_id}",
            json={"incident": incident},
            headers=headers
        )
        response.raise_for_status()
        return response.json().get('incident', {})

    def add_note(
        self,
        incident_id: str,
        content: str,
        from_email: str = None
    ) -> Dict:
        """Add a note to an incident."""
        headers = {'From': from_email or self.default_from_email}

        response = self.session.post(
            f"{self.api_url}/incidents/{incident_id}/notes",
            json={"note": {"content": content}},
            headers=headers
        )
        response.raise_for_status()
        return response.json().get('note', {})

    # REST API - Services
    def list_services(self, limit: int = 25) -> List[Dict]:
        """List services."""
        response = self.session.get(
            f"{self.api_url}/services",
            params={'limit': limit}
        )
        response.raise_for_status()
        return response.json().get('services', [])

    def get_service(self, service_id: str) -> Dict:
        """Get service details."""
        response = self.session.get(f"{self.api_url}/services/{service_id}")
        response.raise_for_status()
        return response.json().get('service', {})

    # REST API - Users & On-Call
    def list_users(self, limit: int = 25) -> List[Dict]:
        """List users."""
        response = self.session.get(
            f"{self.api_url}/users",
            params={'limit': limit}
        )
        response.raise_for_status()
        return response.json().get('users', [])

    def get_oncalls(
        self,
        schedule_ids: List[str] = None,
        escalation_policy_ids: List[str] = None,
        since: str = None,
        until: str = None
    ) -> List[Dict]:
        """Get on-call information."""
        params = {}
        if schedule_ids:
            params['schedule_ids[]'] = schedule_ids
        if escalation_policy_ids:
            params['escalation_policy_ids[]'] = escalation_policy_ids
        if since:
            params['since'] = since
        if until:
            params['until'] = until

        response = self.session.get(f"{self.api_url}/oncalls", params=params)
        response.raise_for_status()
        return response.json().get('oncalls', [])

    # REST API - Escalation Policies
    def list_escalation_policies(self, limit: int = 25) -> List[Dict]:
        """List escalation policies."""
        response = self.session.get(
            f"{self.api_url}/escalation_policies",
            params={'limit': limit}
        )
        response.raise_for_status()
        return response.json().get('escalation_policies', [])

    # REST API - Schedules
    def list_schedules(self, limit: int = 25) -> List[Dict]:
        """List schedules."""
        response = self.session.get(
            f"{self.api_url}/schedules",
            params={'limit': limit}
        )
        response.raise_for_status()
        return response.json().get('schedules', [])

    # Utility methods
    def trigger_alert(
        self,
        alert_name: str,
        severity: str,
        description: str,
        source: str = "devops-chatbot",
        runbook_url: str = None,
        dashboard_url: str = None,
        labels: Dict = None
    ) -> Dict:
        """Trigger a formatted DevOps alert."""
        custom_details = labels or {}
        custom_details['description'] = description

        links = []
        if runbook_url:
            links.append({"href": runbook_url, "text": "Runbook"})
        if dashboard_url:
            links.append({"href": dashboard_url, "text": "Dashboard"})

        return self.trigger_event(
            summary=f"[{severity.upper()}] {alert_name}",
            severity=severity,
            source=source,
            dedup_key=f"{source}-{alert_name}",
            custom_details=custom_details,
            links=links if links else None
        )

    def get_active_incidents_count(self) -> int:
        """Get count of active (triggered/acknowledged) incidents."""
        incidents = self.list_incidents(
            statuses=['triggered', 'acknowledged'],
            limit=100
        )
        return len(incidents)

    def who_is_oncall(self, escalation_policy_id: str = None) -> List[Dict]:
        """Get current on-call users."""
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        oncalls = self.get_oncalls(
            escalation_policy_ids=[escalation_policy_id] if escalation_policy_id else None,
            since=now.isoformat() + 'Z',
            until=(now + timedelta(minutes=1)).isoformat() + 'Z'
        )

        return [
            {
                'name': oc['user']['summary'],
                'email': oc['user'].get('email'),
                'escalation_level': oc['escalation_level'],
                'schedule': oc.get('schedule', {}).get('summary', 'Direct assignment')
            }
            for oc in oncalls
        ]
