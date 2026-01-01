"""
Grafana API Client
Connect to Grafana for dashboards and alerts
"""

import requests
from typing import Optional, Dict, List, Any
import json


class GrafanaClient:
    """Client for Grafana API interactions."""

    def __init__(self, url: str, api_key: str = None, username: str = None, password: str = None):
        """
        Initialize Grafana client.

        Args:
            url: Grafana server URL (e.g., http://localhost:3000)
            api_key: API key for authentication
            username: Basic auth username
            password: Basic auth password
        """
        self.url = url.rstrip('/')
        self.session = requests.Session()

        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        elif username and password:
            self.session.auth = (username, password)

        self.session.headers['Content-Type'] = 'application/json'

    # Dashboard Operations
    def get_dashboards(self, folder_id: int = None, query: str = None) -> List[Dict]:
        """Search for dashboards."""
        params = {}
        if folder_id:
            params['folderIds'] = folder_id
        if query:
            params['query'] = query

        response = self.session.get(f"{self.url}/api/search", params=params)
        response.raise_for_status()
        return response.json()

    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """Get dashboard by UID."""
        response = self.session.get(f"{self.url}/api/dashboards/uid/{uid}")
        response.raise_for_status()
        return response.json()

    def create_dashboard(self, dashboard: Dict, folder_id: int = 0, overwrite: bool = False) -> Dict:
        """Create or update a dashboard."""
        payload = {
            'dashboard': dashboard,
            'folderId': folder_id,
            'overwrite': overwrite
        }
        response = self.session.post(
            f"{self.url}/api/dashboards/db",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def delete_dashboard(self, uid: str) -> Dict:
        """Delete dashboard by UID."""
        response = self.session.delete(f"{self.url}/api/dashboards/uid/{uid}")
        response.raise_for_status()
        return response.json()

    # Folder Operations
    def get_folders(self) -> List[Dict]:
        """Get all folders."""
        response = self.session.get(f"{self.url}/api/folders")
        response.raise_for_status()
        return response.json()

    def create_folder(self, title: str, uid: str = None) -> Dict:
        """Create a new folder."""
        payload = {'title': title}
        if uid:
            payload['uid'] = uid

        response = self.session.post(f"{self.url}/api/folders", json=payload)
        response.raise_for_status()
        return response.json()

    # Datasource Operations
    def get_datasources(self) -> List[Dict]:
        """Get all datasources."""
        response = self.session.get(f"{self.url}/api/datasources")
        response.raise_for_status()
        return response.json()

    def get_datasource(self, uid: str) -> Dict:
        """Get datasource by UID."""
        response = self.session.get(f"{self.url}/api/datasources/uid/{uid}")
        response.raise_for_status()
        return response.json()

    def create_datasource(self, datasource: Dict) -> Dict:
        """Create a new datasource."""
        response = self.session.post(f"{self.url}/api/datasources", json=datasource)
        response.raise_for_status()
        return response.json()

    def test_datasource(self, uid: str) -> Dict:
        """Test a datasource connection."""
        response = self.session.get(f"{self.url}/api/datasources/uid/{uid}/health")
        response.raise_for_status()
        return response.json()

    # Alert Operations
    def get_alert_rules(self) -> List[Dict]:
        """Get all alert rules."""
        response = self.session.get(f"{self.url}/api/v1/provisioning/alert-rules")
        response.raise_for_status()
        return response.json()

    def get_alert_rule(self, uid: str) -> Dict:
        """Get alert rule by UID."""
        response = self.session.get(f"{self.url}/api/v1/provisioning/alert-rules/{uid}")
        response.raise_for_status()
        return response.json()

    def create_alert_rule(self, rule: Dict) -> Dict:
        """Create an alert rule."""
        response = self.session.post(
            f"{self.url}/api/v1/provisioning/alert-rules",
            json=rule
        )
        response.raise_for_status()
        return response.json()

    def get_contact_points(self) -> List[Dict]:
        """Get all contact points."""
        response = self.session.get(f"{self.url}/api/v1/provisioning/contact-points")
        response.raise_for_status()
        return response.json()

    # Annotation Operations
    def get_annotations(self, dashboard_id: int = None, panel_id: int = None,
                        from_time: int = None, to_time: int = None) -> List[Dict]:
        """Get annotations."""
        params = {}
        if dashboard_id:
            params['dashboardId'] = dashboard_id
        if panel_id:
            params['panelId'] = panel_id
        if from_time:
            params['from'] = from_time
        if to_time:
            params['to'] = to_time

        response = self.session.get(f"{self.url}/api/annotations", params=params)
        response.raise_for_status()
        return response.json()

    def create_annotation(self, text: str, tags: List[str] = None,
                         dashboard_id: int = None, panel_id: int = None,
                         time: int = None, time_end: int = None) -> Dict:
        """Create an annotation."""
        payload = {'text': text}
        if tags:
            payload['tags'] = tags
        if dashboard_id:
            payload['dashboardId'] = dashboard_id
        if panel_id:
            payload['panelId'] = panel_id
        if time:
            payload['time'] = time
        if time_end:
            payload['timeEnd'] = time_end

        response = self.session.post(f"{self.url}/api/annotations", json=payload)
        response.raise_for_status()
        return response.json()

    # User & Organization
    def get_current_user(self) -> Dict:
        """Get current user."""
        response = self.session.get(f"{self.url}/api/user")
        response.raise_for_status()
        return response.json()

    def get_org(self) -> Dict:
        """Get current organization."""
        response = self.session.get(f"{self.url}/api/org")
        response.raise_for_status()
        return response.json()

    # Health Check
    def health_check(self) -> bool:
        """Check if Grafana is healthy."""
        try:
            response = self.session.get(f"{self.url}/api/health")
            return response.status_code == 200
        except Exception:
            return False

    # Helper methods
    def create_prometheus_datasource(self, name: str, prometheus_url: str, is_default: bool = False) -> Dict:
        """Create a Prometheus datasource."""
        datasource = {
            'name': name,
            'type': 'prometheus',
            'url': prometheus_url,
            'access': 'proxy',
            'isDefault': is_default
        }
        return self.create_datasource(datasource)

    def create_loki_datasource(self, name: str, loki_url: str, is_default: bool = False) -> Dict:
        """Create a Loki datasource."""
        datasource = {
            'name': name,
            'type': 'loki',
            'url': loki_url,
            'access': 'proxy',
            'isDefault': is_default
        }
        return self.create_datasource(datasource)
