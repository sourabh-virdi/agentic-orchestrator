# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report them responsibly:

1. **Email:** security@agentic-orchestrator.dev
2. **Subject:** `[SECURITY] Brief description`
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a detailed response
within 7 days.

## Security Practices

### Secrets Management

- **Never** commit secrets, API keys, or credentials to the repository
- Use `.env` files for local development (`.env` is in `.gitignore`)
- Production secrets should be managed via:
  - **HashiCorp Vault** (recommended)
  - **AWS Secrets Manager**
  - **Azure Key Vault**
  - Kubernetes Secrets (encrypted at rest)

### Environment Variables

Required secrets (see `.env.example`):

| Variable | Description | Where to Store |
|----------|-------------|----------------|
| `DATABASE_URL` | PostgreSQL connection string | Vault / Secrets Manager |
| `REDIS_URL` | Redis connection string | Vault / Secrets Manager |
| `JWT_SECRET` | JWT signing key (min 256-bit) | Vault / Secrets Manager |
| `OPENAI_API_KEY` | LLM API key (if using) | Vault / Secrets Manager |

### IAM / Access Control

Minimal IAM policy for AWS deployment:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "elasticache:DescribeCacheClusters"
      ],
      "Resource": "arn:aws:*:*:*:agentic-orchestrator-*"
    }
  ]
}
```

### Container Security

- Base image: `python:3.11-slim` (minimal attack surface)
- Container runs as non-root user (`appuser`, UID 1000)
- No `--privileged` flag
- Read-only root filesystem where possible
- Health checks enabled

### Network Security

- Internal services communicate on Docker network (not exposed)
- Only the API port (8000) is exposed externally
- TLS termination at load balancer / ingress
- Database connections use TLS (`sslmode=require`)

### Input Validation

- All API inputs validated via Pydantic models
- SQL injection prevented by SQLAlchemy parameterized queries
- Rate limiting: 100 requests/minute per client IP

### Audit Trail

- All agent actions logged to immutable audit table
- Audit log is append-only (no UPDATE/DELETE in production)
- Retention: 90 days default, configurable

## Dependency Security

- Dependencies pinned to specific versions
- Dependabot enabled for automated security updates
- `pip-audit` runs in CI to catch known vulnerabilities
