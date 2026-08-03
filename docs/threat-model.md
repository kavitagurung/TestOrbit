# Threat model

Primary threats: SSRF, credential leakage, prompt injection in web content, untrusted HTML, webhook leakage, overly broad CORS, unauthorized scheduler access, and prohibited crawling. Controls include HTTPS/public-IP validation, bounded responses/timeouts, server-only environment variables, content delimiting, structured AI validation, audit logging, restricted source types, and a read-only MCP surface.

