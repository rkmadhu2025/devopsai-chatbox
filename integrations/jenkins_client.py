"""
Jenkins API Client
Connect to Jenkins for CI/CD operations
"""

import requests
from typing import Optional, Dict, List, Any
import time


class JenkinsClient:
    """Client for Jenkins API interactions."""

    def __init__(self, url: str, username: str, api_token: str):
        """
        Initialize Jenkins client.

        Args:
            url: Jenkins server URL (e.g., http://localhost:8080)
            username: Jenkins username
            api_token: Jenkins API token
        """
        self.url = url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers['Content-Type'] = 'application/json'

    def _get_crumb(self) -> Dict[str, str]:
        """Get CSRF crumb for POST requests."""
        try:
            response = self.session.get(f"{self.url}/crumbIssuer/api/json")
            if response.status_code == 200:
                crumb = response.json()
                return {crumb['crumbRequestField']: crumb['crumb']}
        except Exception:
            pass
        return {}

    # Job Operations
    def get_jobs(self, folder: str = None) -> List[Dict]:
        """Get all jobs."""
        url = f"{self.url}/api/json?tree=jobs[name,url,color]"
        if folder:
            url = f"{self.url}/job/{folder}/api/json?tree=jobs[name,url,color]"

        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('jobs', [])

    def get_job(self, name: str) -> Dict:
        """Get job details."""
        response = self.session.get(f"{self.url}/job/{name}/api/json")
        response.raise_for_status()
        return response.json()

    def get_job_config(self, name: str) -> str:
        """Get job configuration XML."""
        response = self.session.get(f"{self.url}/job/{name}/config.xml")
        response.raise_for_status()
        return response.text

    def create_job(self, name: str, config_xml: str) -> bool:
        """Create a new job."""
        headers = {'Content-Type': 'application/xml'}
        headers.update(self._get_crumb())
        response = self.session.post(
            f"{self.url}/createItem?name={name}",
            data=config_xml,
            headers=headers
        )
        return response.status_code == 200

    def delete_job(self, name: str) -> bool:
        """Delete a job."""
        headers = self._get_crumb()
        response = self.session.post(
            f"{self.url}/job/{name}/doDelete",
            headers=headers
        )
        return response.status_code in [200, 302]

    def enable_job(self, name: str) -> bool:
        """Enable a job."""
        headers = self._get_crumb()
        response = self.session.post(
            f"{self.url}/job/{name}/enable",
            headers=headers
        )
        return response.status_code in [200, 302]

    def disable_job(self, name: str) -> bool:
        """Disable a job."""
        headers = self._get_crumb()
        response = self.session.post(
            f"{self.url}/job/{name}/disable",
            headers=headers
        )
        return response.status_code in [200, 302]

    # Build Operations
    def build_job(self, name: str, parameters: Dict[str, str] = None) -> int:
        """Trigger a build."""
        headers = self._get_crumb()

        if parameters:
            response = self.session.post(
                f"{self.url}/job/{name}/buildWithParameters",
                params=parameters,
                headers=headers
            )
        else:
            response = self.session.post(
                f"{self.url}/job/{name}/build",
                headers=headers
            )

        if response.status_code in [200, 201]:
            # Get queue item location
            queue_url = response.headers.get('Location', '')
            if queue_url:
                return self._get_build_number_from_queue(queue_url)
        return -1

    def _get_build_number_from_queue(self, queue_url: str, timeout: int = 60) -> int:
        """Wait for build to start and get build number."""
        queue_api = f"{queue_url}api/json"
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self.session.get(queue_api)
            if response.status_code == 200:
                data = response.json()
                if 'executable' in data and data['executable']:
                    return data['executable']['number']
            time.sleep(2)
        return -1

    def get_build(self, job_name: str, build_number: int) -> Dict:
        """Get build details."""
        response = self.session.get(
            f"{self.url}/job/{job_name}/{build_number}/api/json"
        )
        response.raise_for_status()
        return response.json()

    def get_last_build(self, job_name: str) -> Dict:
        """Get last build details."""
        response = self.session.get(
            f"{self.url}/job/{job_name}/lastBuild/api/json"
        )
        response.raise_for_status()
        return response.json()

    def get_build_console(self, job_name: str, build_number: int) -> str:
        """Get build console output."""
        response = self.session.get(
            f"{self.url}/job/{job_name}/{build_number}/consoleText"
        )
        response.raise_for_status()
        return response.text

    def stop_build(self, job_name: str, build_number: int) -> bool:
        """Stop a running build."""
        headers = self._get_crumb()
        response = self.session.post(
            f"{self.url}/job/{job_name}/{build_number}/stop",
            headers=headers
        )
        return response.status_code in [200, 302]

    def get_build_status(self, job_name: str, build_number: int) -> str:
        """Get build status (SUCCESS, FAILURE, UNSTABLE, ABORTED, BUILDING)."""
        build = self.get_build(job_name, build_number)
        if build.get('building'):
            return 'BUILDING'
        return build.get('result', 'UNKNOWN')

    # Queue Operations
    def get_queue(self) -> List[Dict]:
        """Get build queue."""
        response = self.session.get(f"{self.url}/queue/api/json")
        response.raise_for_status()
        return response.json().get('items', [])

    def cancel_queue_item(self, item_id: int) -> bool:
        """Cancel a queued item."""
        headers = self._get_crumb()
        response = self.session.post(
            f"{self.url}/queue/cancelItem?id={item_id}",
            headers=headers
        )
        return response.status_code in [200, 204, 302]

    # Node Operations
    def get_nodes(self) -> List[Dict]:
        """Get all nodes/agents."""
        response = self.session.get(
            f"{self.url}/computer/api/json?tree=computer[displayName,offline,temporarilyOffline,numExecutors,executors[idle]]"
        )
        response.raise_for_status()
        return response.json().get('computer', [])

    def get_node(self, name: str) -> Dict:
        """Get node details."""
        response = self.session.get(f"{self.url}/computer/{name}/api/json")
        response.raise_for_status()
        return response.json()

    # Plugin Operations
    def get_plugins(self) -> List[Dict]:
        """Get installed plugins."""
        response = self.session.get(
            f"{self.url}/pluginManager/api/json?tree=plugins[shortName,version,active,enabled]"
        )
        response.raise_for_status()
        return response.json().get('plugins', [])

    # System Operations
    def get_system_info(self) -> Dict:
        """Get Jenkins system information."""
        response = self.session.get(f"{self.url}/api/json")
        response.raise_for_status()
        return response.json()

    def quiet_down(self) -> bool:
        """Prepare Jenkins for shutdown (quiet mode)."""
        headers = self._get_crumb()
        response = self.session.post(
            f"{self.url}/quietDown",
            headers=headers
        )
        return response.status_code in [200, 302]

    def cancel_quiet_down(self) -> bool:
        """Cancel quiet mode."""
        headers = self._get_crumb()
        response = self.session.post(
            f"{self.url}/cancelQuietDown",
            headers=headers
        )
        return response.status_code in [200, 302]

    def restart(self, safe: bool = True) -> bool:
        """Restart Jenkins."""
        headers = self._get_crumb()
        endpoint = "safeRestart" if safe else "restart"
        response = self.session.post(
            f"{self.url}/{endpoint}",
            headers=headers
        )
        return response.status_code in [200, 302]

    # Health Check
    def health_check(self) -> bool:
        """Check if Jenkins is healthy."""
        try:
            response = self.session.get(f"{self.url}/api/json")
            return response.status_code == 200
        except Exception:
            return False
