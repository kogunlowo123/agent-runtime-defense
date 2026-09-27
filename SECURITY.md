# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

For critical or high-severity findings, use GitHub's private security advisory feature:
[Report a security vulnerability](https://github.com/kogunlowo123/agent-runtime-defense/security/advisories/new)

For low/medium-severity findings, email: security@example.com

### Response SLA

| Severity | Acknowledge | Triage | Remediation |
|----------|-------------|--------|-------------|
| Critical | 24 hours    | 48 hours | 7 days   |
| High     | 24 hours    | 72 hours | 30 days  |
| Medium   | 48 hours    | 7 days   | 90 days  |
| Low      | 7 days      | 14 days  | 180 days |

## Scope

In scope:
- API authentication and authorization bypass
- Prompt injection vulnerabilities in agent pipelines
- Data exfiltration through RAG or agent tool abuse
- T2 approval gate bypass
- Infrastructure misconfiguration (Terraform, AKS)
- Dependency vulnerabilities with active exploits

Out of scope:
- Denial of service via legitimate API usage
- Issues requiring physical access to infrastructure

## Security Controls

- All API endpoints require JWT authentication
- T2 isolation actions require approval tokens with short TTL
- OPA policy enforces caller scope and anomaly score thresholds
- Secrets managed via Azure Key Vault with RBAC
- All container images scanned by Trivy before deployment
- SIGMA detection rules for anomalous agent behavior
- Azure Sentinel integration for SIEM correlation
