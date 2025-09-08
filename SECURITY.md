# Security Policy

## Supported Versions

We actively support the following versions of TomlEv with security updates:

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | :white_check_mark: |
| 0.9.x   | :x:                |
| < 0.9   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. Please follow these steps to report security issues:

### Private Reporting

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to: **m+security@bubelich.com**

Include the following information:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- **Initial Response**: Within 48 hours of receiving your report
- **Status Update**: Within 1 week with an estimated timeline for fixes
- **Resolution**: Security patches will be prioritized and released as soon as possible

### Security Best Practices

When using TomlEv in production:

1. **Input Validation**: Always validate configuration data from untrusted sources
2. **File Permissions**: Ensure configuration files have appropriate read permissions
3. **Environment Variables**: Be cautious with sensitive data in environment variables
4. **Regular Updates**: Keep TomlEv updated to the latest version
5. **Dependency Scanning**: Regularly scan dependencies for known vulnerabilities

### Security Features

TomlEv includes several security features:

- **Input Sanitization**: Automatic validation of configuration types
- **Path Traversal Protection**: Safe file path handling
- **Strict Mode**: Optional strict validation to catch configuration errors
- **Type Safety**: Strong typing prevents many common security issues

### Security Testing

We employ multiple layers of security testing:

- **Static Analysis**: Automated code scanning with Bandit
- **Dependency Scanning**: Regular vulnerability scans with Safety
- **Code Review**: All changes undergo security-focused code review
- **Fuzzing**: Property-based testing with Hypothesis

## Responsible Disclosure

We follow responsible disclosure practices and ask that you:

- Give us reasonable time to investigate and fix the issue before public disclosure
- Avoid privacy violations, destruction of data, and disruption of services
- Only interact with accounts you own or have explicit permission to access

## Recognition

We maintain a security researchers hall of fame for those who responsibly disclose vulnerabilities. Contributors will be
acknowledged (with permission) in:

- Release notes for the fixed version
- Security advisory documentation
- Project README (optional)

Thank you for helping keep TomlEv and our users safe!
