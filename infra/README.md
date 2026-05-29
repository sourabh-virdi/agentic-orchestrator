# Infrastructure

This directory contains infrastructure-as-code for deploying the Agentic Orchestrator.

## Structure

```
infra/
├── terraform/          # Terraform configs for cloud deployment
│   ├── main.tf         # Main resource definitions
│   ├── variables.tf    # Input variables
│   ├── outputs.tf      # Output values
│   └── environments/
│       ├── dev.tfvars   # Development overrides
│       └── prod.tfvars  # Production overrides
├── helm/               # Kubernetes Helm chart
│   └── agentic-orchestrator/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── prometheus/         # Prometheus configuration
│   └── prometheus.yml
└── grafana/            # Grafana dashboard and provisioning
    ├── dashboards/
    └── provisioning/
```

## Quick Start

### Terraform (AWS)

```bash
cd infra/terraform
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

### Helm (Kubernetes)

```bash
helm install orchestrator infra/helm/agentic-orchestrator \
  --namespace orchestrator \
  --create-namespace \
  -f infra/helm/agentic-orchestrator/values.yaml
```

## Cost Control

Both Terraform and Helm configs include cost-control flags:
- **Terraform:** `instance_type`, `min_capacity`, `max_capacity` variables
- **Helm:** `resources.limits`, `autoscaling.maxReplicas` in values.yaml

For development, use minimal resource configurations to keep costs low.
