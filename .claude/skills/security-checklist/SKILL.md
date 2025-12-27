---
name: security-checklist
description: Security audit checklists, production deployment checklists, quality gates, and security standards. Load this skill before production deployment or when implementing security-sensitive features.
---

This skill provides comprehensive security and deployment checklists. Load before any production deployment or when implementing security features.

## Security Audit Checklist

### Input Validation
- [ ] All user inputs sanitized and validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Path traversal prevention
- [ ] File upload validation (type, size, content)

### Authentication & Authorization
- [ ] Secure session management
- [ ] Password hashing (bcrypt/argon2)
- [ ] Rate limiting on auth endpoints
- [ ] Role-based access control implemented
- [ ] JWT tokens properly validated and expired
- [ ] OAuth flows secure (PKCE for public clients)

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] TLS/SSL for all data in transit
- [ ] PII handled according to regulations
- [ ] Database credentials secured
- [ ] Backup encryption enabled

### Secret Management
- [ ] No hardcoded secrets in code
- [ ] Environment variables for configuration
- [ ] Secrets rotation capability
- [ ] Access to secrets audited
- [ ] .env files in .gitignore

### Error Handling
- [ ] No sensitive info in error messages
- [ ] Stack traces hidden in production
- [ ] Errors logged securely
- [ ] User-friendly error messages

### Dependencies
- [ ] All dependencies up to date
- [ ] Vulnerability scan completed
- [ ] No known CVEs in dependencies
- [ ] Lock files committed

### Logging & Monitoring
- [ ] Security events logged
- [ ] Sensitive data excluded from logs
- [ ] Log injection prevention
- [ ] Anomaly detection configured

## Production Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (unit, integration, e2e)
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] Code review completed
- [ ] Documentation updated

### Infrastructure
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] CDN configured (if applicable)
- [ ] Load balancer health checks
- [ ] Auto-scaling configured

### Database
- [ ] Migrations tested
- [ ] Backup procedures tested
- [ ] Connection pooling configured
- [ ] Indexes verified

### Monitoring
- [ ] Health endpoints configured
- [ ] Error tracking enabled
- [ ] Performance monitoring active
- [ ] Alerting configured

### Recovery
- [ ] Rollback procedure documented
- [ ] Disaster recovery plan
- [ ] Data restoration tested

## Quality Gates

All must pass before deployment:

| Gate | Requirement |
|------|-------------|
| Code Quality | Linting passes, no code smells |
| Test Coverage | ≥80% on critical paths |
| Security | No high/critical vulnerabilities |
| Performance | Response times within requirements |
| Documentation | Setup, API, troubleshooting complete |

## Security Standards (Non-Negotiable)

1. **Input Validation**: Sanitize ALL user inputs
2. **Authentication**: Proper session management
3. **Authorization**: RBAC where needed
4. **Data Protection**: Encrypt sensitive data
5. **Secret Management**: Never hardcode secrets
6. **Error Handling**: Don't expose sensitive info
7. **Dependencies**: Regular security updates
8. **Logging**: Log security events, sanitize sensitive data

## Common Vulnerabilities to Check

- OWASP Top 10 coverage
- Injection flaws (SQL, NoSQL, LDAP, OS)
- Broken authentication
- Sensitive data exposure
- XML external entities (XXE)
- Broken access control
- Security misconfiguration
- Cross-site scripting (XSS)
- Insecure deserialization
- Using components with known vulnerabilities
- Insufficient logging & monitoring

## Emergency Response

**If security incident detected:**
1. Isolate affected systems
2. Preserve evidence/logs
3. Assess scope of breach
4. Notify appropriate parties
5. Implement fixes
6. Document incident
7. Post-mortem review
