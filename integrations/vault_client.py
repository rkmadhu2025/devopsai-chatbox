"""
HashiCorp Vault API Client
Connect to Vault for secrets management
"""

import requests
from typing import Optional, Dict, List, Any


class VaultClient:
    """Client for HashiCorp Vault API interactions."""

    def __init__(self, url: str, token: str = None, namespace: str = None):
        """
        Initialize Vault client.

        Args:
            url: Vault server URL (e.g., http://localhost:8200)
            token: Vault token for authentication
            namespace: Vault namespace (Enterprise feature)
        """
        self.url = url.rstrip('/')
        self.session = requests.Session()

        if token:
            self.session.headers['X-Vault-Token'] = token
        if namespace:
            self.session.headers['X-Vault-Namespace'] = namespace

        self.session.headers['Content-Type'] = 'application/json'

    def set_token(self, token: str):
        """Set or update the Vault token."""
        self.session.headers['X-Vault-Token'] = token

    # Auth Methods
    def login_userpass(self, username: str, password: str, mount: str = "userpass") -> Dict:
        """Login with userpass auth method."""
        response = self.session.post(
            f"{self.url}/v1/auth/{mount}/login/{username}",
            json={'password': password}
        )
        response.raise_for_status()
        data = response.json()
        self.set_token(data['auth']['client_token'])
        return data

    def login_approle(self, role_id: str, secret_id: str, mount: str = "approle") -> Dict:
        """Login with AppRole auth method."""
        response = self.session.post(
            f"{self.url}/v1/auth/{mount}/login",
            json={'role_id': role_id, 'secret_id': secret_id}
        )
        response.raise_for_status()
        data = response.json()
        self.set_token(data['auth']['client_token'])
        return data

    def login_kubernetes(self, role: str, jwt: str, mount: str = "kubernetes") -> Dict:
        """Login with Kubernetes auth method."""
        response = self.session.post(
            f"{self.url}/v1/auth/{mount}/login",
            json={'role': role, 'jwt': jwt}
        )
        response.raise_for_status()
        data = response.json()
        self.set_token(data['auth']['client_token'])
        return data

    # KV Secrets Engine (v2)
    def kv_read(self, path: str, mount: str = "secret", version: int = None) -> Dict:
        """Read a secret from KV v2."""
        url = f"{self.url}/v1/{mount}/data/{path}"
        params = {}
        if version:
            params['version'] = version

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()['data']['data']

    def kv_write(self, path: str, data: Dict, mount: str = "secret", cas: int = None) -> Dict:
        """Write a secret to KV v2."""
        payload = {'data': data}
        if cas is not None:
            payload['options'] = {'cas': cas}

        response = self.session.post(
            f"{self.url}/v1/{mount}/data/{path}",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def kv_delete(self, path: str, mount: str = "secret", versions: List[int] = None) -> bool:
        """Delete a secret from KV v2."""
        if versions:
            response = self.session.post(
                f"{self.url}/v1/{mount}/delete/{path}",
                json={'versions': versions}
            )
        else:
            response = self.session.delete(f"{self.url}/v1/{mount}/data/{path}")
        return response.status_code == 204

    def kv_list(self, path: str = "", mount: str = "secret") -> List[str]:
        """List secrets at a path."""
        response = self.session.request(
            'LIST',
            f"{self.url}/v1/{mount}/metadata/{path}"
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()['data']['keys']

    def kv_metadata(self, path: str, mount: str = "secret") -> Dict:
        """Get metadata for a secret."""
        response = self.session.get(f"{self.url}/v1/{mount}/metadata/{path}")
        response.raise_for_status()
        return response.json()['data']

    # Database Secrets Engine
    def db_get_creds(self, role: str, mount: str = "database") -> Dict:
        """Get dynamic database credentials."""
        response = self.session.get(f"{self.url}/v1/{mount}/creds/{role}")
        response.raise_for_status()
        return response.json()['data']

    # AWS Secrets Engine
    def aws_get_creds(self, role: str, mount: str = "aws") -> Dict:
        """Get AWS credentials."""
        response = self.session.get(f"{self.url}/v1/{mount}/creds/{role}")
        response.raise_for_status()
        return response.json()['data']

    # PKI Secrets Engine
    def pki_issue_cert(self, role: str, common_name: str, mount: str = "pki",
                       alt_names: List[str] = None, ttl: str = None) -> Dict:
        """Issue a certificate."""
        payload = {'common_name': common_name}
        if alt_names:
            payload['alt_names'] = ','.join(alt_names)
        if ttl:
            payload['ttl'] = ttl

        response = self.session.post(
            f"{self.url}/v1/{mount}/issue/{role}",
            json=payload
        )
        response.raise_for_status()
        return response.json()['data']

    def pki_sign(self, role: str, csr: str, mount: str = "pki",
                 common_name: str = None, ttl: str = None) -> Dict:
        """Sign a CSR."""
        payload = {'csr': csr}
        if common_name:
            payload['common_name'] = common_name
        if ttl:
            payload['ttl'] = ttl

        response = self.session.post(
            f"{self.url}/v1/{mount}/sign/{role}",
            json=payload
        )
        response.raise_for_status()
        return response.json()['data']

    # Transit Secrets Engine
    def transit_encrypt(self, key: str, plaintext: str, mount: str = "transit") -> str:
        """Encrypt data using Transit."""
        import base64
        response = self.session.post(
            f"{self.url}/v1/{mount}/encrypt/{key}",
            json={'plaintext': base64.b64encode(plaintext.encode()).decode()}
        )
        response.raise_for_status()
        return response.json()['data']['ciphertext']

    def transit_decrypt(self, key: str, ciphertext: str, mount: str = "transit") -> str:
        """Decrypt data using Transit."""
        import base64
        response = self.session.post(
            f"{self.url}/v1/{mount}/decrypt/{key}",
            json={'ciphertext': ciphertext}
        )
        response.raise_for_status()
        return base64.b64decode(response.json()['data']['plaintext']).decode()

    # Token Operations
    def token_lookup_self(self) -> Dict:
        """Lookup current token."""
        response = self.session.get(f"{self.url}/v1/auth/token/lookup-self")
        response.raise_for_status()
        return response.json()['data']

    def token_renew_self(self, increment: str = None) -> Dict:
        """Renew current token."""
        payload = {}
        if increment:
            payload['increment'] = increment

        response = self.session.post(
            f"{self.url}/v1/auth/token/renew-self",
            json=payload
        )
        response.raise_for_status()
        return response.json()['auth']

    def token_create(self, policies: List[str] = None, ttl: str = None,
                     renewable: bool = True, metadata: Dict = None) -> Dict:
        """Create a new token."""
        payload = {'renewable': renewable}
        if policies:
            payload['policies'] = policies
        if ttl:
            payload['ttl'] = ttl
        if metadata:
            payload['metadata'] = metadata

        response = self.session.post(
            f"{self.url}/v1/auth/token/create",
            json=payload
        )
        response.raise_for_status()
        return response.json()['auth']

    # Policy Operations
    def policy_list(self) -> List[str]:
        """List all policies."""
        response = self.session.get(f"{self.url}/v1/sys/policies/acl")
        response.raise_for_status()
        return response.json()['data']['keys']

    def policy_read(self, name: str) -> str:
        """Read a policy."""
        response = self.session.get(f"{self.url}/v1/sys/policies/acl/{name}")
        response.raise_for_status()
        return response.json()['data']['policy']

    def policy_write(self, name: str, policy: str) -> bool:
        """Write a policy."""
        response = self.session.put(
            f"{self.url}/v1/sys/policies/acl/{name}",
            json={'policy': policy}
        )
        return response.status_code == 204

    # System Operations
    def sys_health(self) -> Dict:
        """Get Vault health status."""
        response = self.session.get(f"{self.url}/v1/sys/health")
        return response.json()

    def sys_seal_status(self) -> Dict:
        """Get seal status."""
        response = self.session.get(f"{self.url}/v1/sys/seal-status")
        response.raise_for_status()
        return response.json()

    def sys_mounts(self) -> Dict:
        """List secret engine mounts."""
        response = self.session.get(f"{self.url}/v1/sys/mounts")
        response.raise_for_status()
        return response.json()['data']

    def sys_auth_list(self) -> Dict:
        """List auth methods."""
        response = self.session.get(f"{self.url}/v1/sys/auth")
        response.raise_for_status()
        return response.json()['data']

    # Health Check
    def health_check(self) -> bool:
        """Check if Vault is healthy and unsealed."""
        try:
            response = self.session.get(f"{self.url}/v1/sys/health")
            return response.status_code == 200
        except Exception:
            return False

    def is_sealed(self) -> bool:
        """Check if Vault is sealed."""
        status = self.sys_seal_status()
        return status.get('sealed', True)
