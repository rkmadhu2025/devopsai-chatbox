#!/bin/bash
# =============================================================================
# DEPLOYMENT SCRIPT - DevOps Multi-Agent Chatbot
# =============================================================================
# Usage: ./deploy.sh [build|deploy|all|delete]
# =============================================================================

set -e

# Configuration
IMAGE_NAME="devops-chatbot"
IMAGE_TAG="latest"
NAMESPACE="default"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Build Docker image
build() {
    print_status "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
    cd "$(dirname "$0")/.."
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
    print_status "Docker image built successfully!"
}

# Deploy to Kubernetes
deploy() {
    print_status "Deploying to Kubernetes namespace: ${NAMESPACE}"

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi

    # Apply secrets (make sure to update with real values first!)
    print_warning "Make sure to update secret.yaml with your actual API keys!"
    kubectl apply -f "$(dirname "$0")/secret.yaml"

    # Apply deployment and configmap
    kubectl apply -f "$(dirname "$0")/deployment.yaml"

    # Apply service
    kubectl apply -f "$(dirname "$0")/service.yaml"

    print_status "Deployment complete!"
    print_status "Waiting for pods to be ready..."
    kubectl rollout status deployment/devops-chatbot -n ${NAMESPACE}

    # Get NodePort
    NODE_PORT=$(kubectl get svc devops-chatbot -n ${NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}')
    print_status "Application is accessible at: http://<node-ip>:${NODE_PORT}"
}

# Delete deployment
delete() {
    print_status "Deleting deployment from Kubernetes..."
    kubectl delete -f "$(dirname "$0")/service.yaml" --ignore-not-found
    kubectl delete -f "$(dirname "$0")/deployment.yaml" --ignore-not-found
    kubectl delete -f "$(dirname "$0")/secret.yaml" --ignore-not-found
    print_status "Deployment deleted!"
}

# Show status
status() {
    print_status "Deployment Status:"
    echo "---"
    kubectl get deployment devops-chatbot -n ${NAMESPACE} 2>/dev/null || echo "Deployment not found"
    echo "---"
    kubectl get pods -l app=devops-chatbot -n ${NAMESPACE} 2>/dev/null || echo "No pods found"
    echo "---"
    kubectl get svc devops-chatbot -n ${NAMESPACE} 2>/dev/null || echo "Service not found"
}

# Main
case "${1:-all}" in
    build)
        build
        ;;
    deploy)
        deploy
        ;;
    delete)
        delete
        ;;
    status)
        status
        ;;
    all)
        build
        deploy
        ;;
    *)
        echo "Usage: $0 [build|deploy|all|delete|status]"
        echo "  build  - Build Docker image"
        echo "  deploy - Deploy to Kubernetes"
        echo "  all    - Build and deploy (default)"
        echo "  delete - Remove deployment"
        echo "  status - Show deployment status"
        exit 1
        ;;
esac
