# Security Policy

## Supported Versions

This security policy applies to the PydanticAI Streamlit Financial Research Agent.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Overview

This application handles financial data and integrates with third-party APIs. Please review the following security considerations before deployment.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by:

1. **DO NOT** create a public GitHub issue
2. Email the maintainers directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if available)

We will acknowledge your report within 48 hours and provide a detailed response within 5 business days.

## Known Security Considerations

### API Key Management

- All API keys must be stored in a `.env` file
- **NEVER** commit the `.env` file to version control
- Verify `.env` is in `.gitignore` before committing
- Rotate API keys immediately if exposed

### Data Privacy

- User prompts and agent responses are logged to LogFire for observability
- Conversations may contain sensitive financial information
- LogFire data retention: Review LogFire's privacy policy
- Recommendation: Avoid entering personally identifiable information (PII)

### Deployment Security Checklist

Before deploying to production:

- [ ] Verify `.env` file is NOT committed to git
- [ ] All API keys are valid and have appropriate rate limits
- [ ] HTTPS is configured via reverse proxy
- [ ] Security headers are set (X-Content-Type-Options, X-Frame-Options, etc.)
- [ ] Input validation is enabled (MAX_PROMPT_LENGTH enforced)
- [ ] Dependency vulnerabilities scanned with `pip-audit`
- [ ] Stack trace exposure is disabled in production
- [ ] Rate limiting is configured for all APIs

### API Rate Limits

The application enforces the following rate limits:

- **YFinance:** 10 requests per 60 seconds (enforced by application)
- **Tavily:** Based on your Tavily API plan
- **OpenAI:** Based on your OpenAI API tier

### Input Validation

User input is validated to prevent:

- Prompt injection attacks (via PydanticAI's built-in protections)
- Resource exhaustion (2000 character limit per message)
- Invalid ticker symbols (regex pattern validation)

### Third-Party Dependencies

This application depends on:

- OpenAI API (gpt-4o-mini model)
- Tavily API (web search)
- YFinance (stock data)
- LogFire (observability)
- OLLAMA (optional local LLM)

Each service has its own security policies and data handling practices.

## Security Best Practices for Users

1. **API Key Security**
   - Never share your `.env` file
   - Use API keys with minimum required permissions
   - Rotate keys regularly (every 90 days recommended)
   - Monitor API usage for anomalies

2. **Deployment Security**
   - Deploy behind HTTPS-enabled reverse proxy
   - Use firewall rules to restrict access
   - Enable logging and monitoring
   - Keep dependencies updated

3. **Data Handling**
   - Avoid entering sensitive personal information
   - Do not use for financial advice without verification
   - Review LogFire logs for sensitive data exposure
   - Clear conversation history regularly

## API Key Rotation Procedures

If you suspect an API key has been compromised:

1. **Immediate Actions:**
   - Disable the compromised key in the provider's dashboard
   - Generate a new API key
   - Update `.env` file with new key
   - Restart the application

2. **Investigation:**
   - Review API usage logs for unauthorized access
   - Check LogFire logs for suspicious activity
   - Review git history for accidental commits

3. **Prevention:**
   - Verify `.env` is in `.gitignore`
   - Use pre-commit hooks to scan for secrets
   - Consider using a secrets manager (AWS Secrets Manager, Azure Key Vault)

## Limitations

This application is designed for:

- Single-user sessions (no multi-user authentication)
- Non-production financial research
- Development and demonstration purposes

It is **NOT** designed for:

- Production financial trading systems
- Storing sensitive customer data
- High-security environments requiring compliance (PCI-DSS, HIPAA)

## Security Updates

We are committed to maintaining the security of this application. Security updates will be released as needed.

To stay informed:

- Watch this repository for security advisories
- Review the SECURITY_AUDIT_REPORT.md for detailed findings
- Subscribe to security announcements for dependencies

## Compliance

This application does not currently comply with:

- PCI-DSS (payment card industry standards)
- HIPAA (health information privacy)
- SOC 2 (service organization controls)
- ISO 27001 (information security management)

For compliance requirements, additional controls must be implemented.

## Contact

For security concerns, please contact the project maintainers.

---

**Last Updated:** 2025-12-27
**Next Review:** 2026-03-27 (Quarterly)
