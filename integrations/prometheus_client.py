"""
Prometheus API Client
Connect to Prometheus for metrics queries and alerts
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin


class PrometheusClient:
    """Client for Prometheus API interactions."""

    def __init__(self, url: str, username: str = None, password: str = None):
        """
        Initialize Prometheus client.

        Args:
            url: Prometheus server URL (e.g., http://localhost:9090)
            username: Optional basic auth username
            password: Optional basic auth password
        """
        self.url = url.rstrip('/')
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)

    def query(self, promql: str, time: datetime = None) -> Dict[str, Any]:
        """
        Execute instant query.

        Args:
            promql: PromQL query string
            time: Evaluation time (default: now)

        Returns:
            Query result as dict
        """
        params = {'query': promql}
        if time:
            params['time'] = time.isoformat()

        response = self.session.get(
            f"{self.url}/api/v1/query",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def query_range(
        self,
        promql: str,
        start: datetime,
        end: datetime,
        step: str = "1m"
    ) -> Dict[str, Any]:
        """
        Execute range query.

        Args:
            promql: PromQL query string
            start: Start time
            end: End time
            step: Query resolution step (e.g., "1m", "5m", "1h")

        Returns:
            Query result as dict
        """
        params = {
            'query': promql,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'step': step
        }

        response = self.session.get(
            f"{self.url}/api/v1/query_range",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_targets(self) -> Dict[str, Any]:
        """Get all scrape targets."""
        response = self.session.get(f"{self.url}/api/v1/targets")
        response.raise_for_status()
        return response.json()

    def get_alerts(self) -> Dict[str, Any]:
        """Get active alerts."""
        response = self.session.get(f"{self.url}/api/v1/alerts")
        response.raise_for_status()
        return response.json()

    def get_rules(self) -> Dict[str, Any]:
        """Get alerting and recording rules."""
        response = self.session.get(f"{self.url}/api/v1/rules")
        response.raise_for_status()
        return response.json()

    def get_labels(self) -> List[str]:
        """Get all label names."""
        response = self.session.get(f"{self.url}/api/v1/labels")
        response.raise_for_status()
        return response.json().get('data', [])

    def get_label_values(self, label: str) -> List[str]:
        """Get values for a specific label."""
        response = self.session.get(f"{self.url}/api/v1/label/{label}/values")
        response.raise_for_status()
        return response.json().get('data', [])

    def get_series(self, match: List[str], start: datetime = None, end: datetime = None) -> List[Dict]:
        """Get time series matching selectors."""
        params = {'match[]': match}
        if start:
            params['start'] = start.isoformat()
        if end:
            params['end'] = end.isoformat()

        response = self.session.get(
            f"{self.url}/api/v1/series",
            params=params
        )
        response.raise_for_status()
        return response.json().get('data', [])

    def get_metadata(self, metric: str = None) -> Dict[str, Any]:
        """Get metric metadata."""
        params = {}
        if metric:
            params['metric'] = metric

        response = self.session.get(
            f"{self.url}/api/v1/metadata",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """Check if Prometheus is healthy."""
        try:
            response = self.session.get(f"{self.url}/-/healthy")
            return response.status_code == 200
        except Exception:
            return False

    def ready_check(self) -> bool:
        """Check if Prometheus is ready."""
        try:
            response = self.session.get(f"{self.url}/-/ready")
            return response.status_code == 200
        except Exception:
            return False

    # Helper methods for common queries
    def get_cpu_usage(self, instance: str = None) -> Dict[str, Any]:
        """Get CPU usage percentage."""
        query = '100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        if instance:
            query = f'100 - (avg by(instance)(rate(node_cpu_seconds_total{{mode="idle",instance="{instance}"}}[5m])) * 100)'
        return self.query(query)

    def get_memory_usage(self, instance: str = None) -> Dict[str, Any]:
        """Get memory usage percentage."""
        query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        if instance:
            query = f'(1 - (node_memory_MemAvailable_bytes{{instance="{instance}"}} / node_memory_MemTotal_bytes{{instance="{instance}"}})) * 100'
        return self.query(query)

    def get_disk_usage(self, instance: str = None) -> Dict[str, Any]:
        """Get disk usage percentage."""
        query = '(1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"})) * 100'
        if instance:
            query = f'(1 - (node_filesystem_avail_bytes{{fstype!="tmpfs",instance="{instance}"}} / node_filesystem_size_bytes{{fstype!="tmpfs",instance="{instance}"}})) * 100'
        return self.query(query)

    def get_pod_cpu(self, namespace: str = None) -> Dict[str, Any]:
        """Get Kubernetes pod CPU usage."""
        query = 'sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod, namespace)'
        if namespace:
            query = f'sum(rate(container_cpu_usage_seconds_total{{container!="",namespace="{namespace}"}}[5m])) by (pod, namespace)'
        return self.query(query)

    def get_pod_memory(self, namespace: str = None) -> Dict[str, Any]:
        """Get Kubernetes pod memory usage."""
        query = 'sum(container_memory_working_set_bytes{container!=""}) by (pod, namespace)'
        if namespace:
            query = f'sum(container_memory_working_set_bytes{{container!="",namespace="{namespace}"}}) by (pod, namespace)'
        return self.query(query)
