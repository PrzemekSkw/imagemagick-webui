# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### Do NOT

- Open a public GitHub issue
- Post about it on social media
- Exploit the vulnerability

### Do

1. **Email us** at security@example.com (replace with your actual security email)
2. **Include details**:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### After Resolution

- We will credit you in the release notes (unless you prefer anonymity)
- We may offer a bounty for critical vulnerabilities (at our discretion)

## Security Measures

### ImageMagick Execution

- **Sandboxed**: Commands run in isolated environment
- **Resource Limits**: 2GB memory, 60s timeout
- **Whitelisted Operations**: Only approved operations allowed
- **No Shell Injection**: Commands are parameterized

### File Handling

- **MIME Validation**: Files checked against actual content
- **Size Limits**: Configurable upload limits (default 50MB)
- **Temporary Cleanup**: Auto-deleted after processing
- **Path Traversal Prevention**: Sanitized file paths

### Authentication

- **JWT Tokens**: Short-lived access tokens
- **Password Hashing**: bcrypt with proper work factor
- **Rate Limiting**: Protection against brute force

### Network

- **HTTPS**: Required in production
- **CORS**: Configured for specific origins
- **Headers**: Security headers configured

## Best Practices for Deployment

1. **Change Default Credentials**
   ```env
   SECRET_KEY=generate-a-strong-random-key
   JWT_SECRET=another-strong-random-key
   ```

2. **Use HTTPS**
   - Always use TLS in production
   - Set up proper SSL certificates

3. **Firewall**
   - Only expose necessary ports
   - Use reverse proxy (nginx, traefik)

4. **Updates**
   - Keep Docker images updated
   - Monitor for security advisories

5. **Backups**
   - Regular database backups
   - Store backups securely off-site

## Acknowledgments

We thank the following researchers for responsibly disclosing vulnerabilities:

*No vulnerabilities reported yet.*

---

Thank you for helping keep ImageMagick WebGUI secure!
