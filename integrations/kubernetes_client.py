"""
Kubernetes API Client
Connect to Kubernetes clusters for resource management
"""

from typing import Optional, Dict, List, Any
import json
import yaml

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    HAS_K8S = True
except ImportError:
    HAS_K8S = False


class KubernetesClient:
    """Client for Kubernetes API interactions."""

    def __init__(self, config_file: str = None, context: str = None, in_cluster: bool = False):
        """
        Initialize Kubernetes client.

        Args:
            config_file: Path to kubeconfig file
            context: Kubernetes context to use
            in_cluster: Use in-cluster configuration
        """
        if not HAS_K8S:
            raise ImportError("kubernetes package not installed. Run: pip install kubernetes")

        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config(config_file=config_file, context=context)

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()
        self.custom_objects = client.CustomObjectsApi()

    # Namespace Operations
    def get_namespaces(self) -> List[str]:
        """Get all namespaces."""
        result = self.core_v1.list_namespace()
        return [ns.metadata.name for ns in result.items]

    def create_namespace(self, name: str, labels: Dict[str, str] = None) -> Dict:
        """Create a namespace."""
        body = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=name, labels=labels)
        )
        result = self.core_v1.create_namespace(body)
        return result.to_dict()

    def delete_namespace(self, name: str) -> Dict:
        """Delete a namespace."""
        result = self.core_v1.delete_namespace(name)
        return result.to_dict()

    # Pod Operations
    def get_pods(self, namespace: str = "default", label_selector: str = None) -> List[Dict]:
        """Get pods in a namespace."""
        result = self.core_v1.list_namespaced_pod(namespace, label_selector=label_selector)
        return [pod.to_dict() for pod in result.items]

    def get_pod(self, name: str, namespace: str = "default") -> Dict:
        """Get a specific pod."""
        result = self.core_v1.read_namespaced_pod(name, namespace)
        return result.to_dict()

    def get_pod_logs(self, name: str, namespace: str = "default",
                     container: str = None, tail_lines: int = 100) -> str:
        """Get pod logs."""
        return self.core_v1.read_namespaced_pod_log(
            name, namespace, container=container, tail_lines=tail_lines
        )

    def delete_pod(self, name: str, namespace: str = "default") -> Dict:
        """Delete a pod."""
        result = self.core_v1.delete_namespaced_pod(name, namespace)
        return result.to_dict()

    # Deployment Operations
    def get_deployments(self, namespace: str = "default") -> List[Dict]:
        """Get deployments in a namespace."""
        result = self.apps_v1.list_namespaced_deployment(namespace)
        return [dep.to_dict() for dep in result.items]

    def get_deployment(self, name: str, namespace: str = "default") -> Dict:
        """Get a specific deployment."""
        result = self.apps_v1.read_namespaced_deployment(name, namespace)
        return result.to_dict()

    def create_deployment(self, deployment: Dict, namespace: str = "default") -> Dict:
        """Create a deployment from dict/yaml."""
        result = self.apps_v1.create_namespaced_deployment(namespace, deployment)
        return result.to_dict()

    def scale_deployment(self, name: str, replicas: int, namespace: str = "default") -> Dict:
        """Scale a deployment."""
        body = {'spec': {'replicas': replicas}}
        result = self.apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
        return result.to_dict()

    def restart_deployment(self, name: str, namespace: str = "default") -> Dict:
        """Restart a deployment by updating annotation."""
        from datetime import datetime
        body = {
            'spec': {
                'template': {
                    'metadata': {
                        'annotations': {
                            'kubectl.kubernetes.io/restartedAt': datetime.now().isoformat()
                        }
                    }
                }
            }
        }
        result = self.apps_v1.patch_namespaced_deployment(name, namespace, body)
        return result.to_dict()

    def delete_deployment(self, name: str, namespace: str = "default") -> Dict:
        """Delete a deployment."""
        result = self.apps_v1.delete_namespaced_deployment(name, namespace)
        return result.to_dict()

    # Service Operations
    def get_services(self, namespace: str = "default") -> List[Dict]:
        """Get services in a namespace."""
        result = self.core_v1.list_namespaced_service(namespace)
        return [svc.to_dict() for svc in result.items]

    def get_service(self, name: str, namespace: str = "default") -> Dict:
        """Get a specific service."""
        result = self.core_v1.read_namespaced_service(name, namespace)
        return result.to_dict()

    def create_service(self, service: Dict, namespace: str = "default") -> Dict:
        """Create a service."""
        result = self.core_v1.create_namespaced_service(namespace, service)
        return result.to_dict()

    # ConfigMap Operations
    def get_configmaps(self, namespace: str = "default") -> List[Dict]:
        """Get configmaps in a namespace."""
        result = self.core_v1.list_namespaced_config_map(namespace)
        return [cm.to_dict() for cm in result.items]

    def get_configmap(self, name: str, namespace: str = "default") -> Dict:
        """Get a specific configmap."""
        result = self.core_v1.read_namespaced_config_map(name, namespace)
        return result.to_dict()

    def create_configmap(self, name: str, data: Dict[str, str],
                         namespace: str = "default") -> Dict:
        """Create a configmap."""
        body = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=name),
            data=data
        )
        result = self.core_v1.create_namespaced_config_map(namespace, body)
        return result.to_dict()

    # Secret Operations
    def get_secrets(self, namespace: str = "default") -> List[Dict]:
        """Get secrets in a namespace (names only, not values)."""
        result = self.core_v1.list_namespaced_secret(namespace)
        return [{'name': s.metadata.name, 'type': s.type} for s in result.items]

    def create_secret(self, name: str, data: Dict[str, str],
                      namespace: str = "default", secret_type: str = "Opaque") -> Dict:
        """Create a secret."""
        import base64
        encoded_data = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}
        body = client.V1Secret(
            metadata=client.V1ObjectMeta(name=name),
            type=secret_type,
            data=encoded_data
        )
        result = self.core_v1.create_namespaced_secret(namespace, body)
        return {'name': result.metadata.name, 'type': result.type}

    # Ingress Operations
    def get_ingresses(self, namespace: str = "default") -> List[Dict]:
        """Get ingresses in a namespace."""
        result = self.networking_v1.list_namespaced_ingress(namespace)
        return [ing.to_dict() for ing in result.items]

    # Job Operations
    def get_jobs(self, namespace: str = "default") -> List[Dict]:
        """Get jobs in a namespace."""
        result = self.batch_v1.list_namespaced_job(namespace)
        return [job.to_dict() for job in result.items]

    def create_job(self, job: Dict, namespace: str = "default") -> Dict:
        """Create a job."""
        result = self.batch_v1.create_namespaced_job(namespace, job)
        return result.to_dict()

    # CronJob Operations
    def get_cronjobs(self, namespace: str = "default") -> List[Dict]:
        """Get cronjobs in a namespace."""
        result = self.batch_v1.list_namespaced_cron_job(namespace)
        return [cj.to_dict() for cj in result.items]

    # Events
    def get_events(self, namespace: str = "default", involved_object_name: str = None) -> List[Dict]:
        """Get events in a namespace."""
        result = self.core_v1.list_namespaced_event(namespace)
        events = result.items
        if involved_object_name:
            events = [e for e in events if e.involved_object.name == involved_object_name]
        return [e.to_dict() for e in events]

    # Nodes
    def get_nodes(self) -> List[Dict]:
        """Get all nodes."""
        result = self.core_v1.list_node()
        return [node.to_dict() for node in result.items]

    def get_node(self, name: str) -> Dict:
        """Get a specific node."""
        result = self.core_v1.read_node(name)
        return result.to_dict()

    # Utility methods
    def apply_yaml(self, yaml_content: str, namespace: str = "default") -> List[Dict]:
        """Apply YAML manifest(s)."""
        from kubernetes import utils
        results = []
        for doc in yaml.safe_load_all(yaml_content):
            if doc:
                result = utils.create_from_dict(client.ApiClient(), doc, namespace=namespace)
                results.append(str(result))
        return results

    def get_resource_usage(self, namespace: str = "default") -> Dict[str, Any]:
        """Get resource usage summary for a namespace."""
        pods = self.get_pods(namespace)
        summary = {
            'namespace': namespace,
            'pod_count': len(pods),
            'pods': []
        }
        for pod in pods:
            pod_info = {
                'name': pod['metadata']['name'],
                'status': pod['status']['phase'],
                'containers': len(pod['spec']['containers'])
            }
            summary['pods'].append(pod_info)
        return summary
