# GFWMass - Automated Multi-Domain Proxy System

An automated system for creating and managing a large, distributed proxy surface using Cloudflare, Caddy, and Xray/VLESS.

## Overview

GFWMass automates the creation of hundreds of realistic-looking subdomains and configures them as proxy endpoints. This provides:

- **IP Masking**: All traffic routed through Cloudflare, hiding your origin server
- **Load Distribution**: Traffic spread across hundreds of domains
- **Resilience**: If some domains fail or are blocked, many alternatives remain
- **Easy Management**: Single script handles everything from DNS to server configuration
- **Wildcard TLS**: You supply one wildcard certificate (e.g., via certbot DNS-01), covering all subdomains

## Architecture

```
Client → Cloudflare (cdn-47fh.example.com) → Caddy → Xray/VLESS → Internet
         Cloudflare (signup-hf33.example.com) ↗
         Cloudflare (api-92kl.example.com) ↗
         ... (hundreds more)
```

1. **Domain Generation**: Creates realistic subdomains (e.g., `cdn-47fh`, `signup-hf33`, `api-92kl`)
2. **Cloudflare DNS**: Each subdomain added as a proxied A record via Cloudflare API
3. **Caddy**: Handles HTTPS termination using a wildcard certificate (*.example.com) that you obtain separately (e.g., certbot DNS-01)
4. **Xray/VLESS over WebSocket (WS)**: Single VLESS+WS endpoint serving all domains
5. **Subscription**: Base64-encoded link containing all proxy endpoints

### Key Features

- **Wildcard Certificate**: Uses a single wildcard certificate (*.example.com) you provide (certbot DNS-01 recommended)
- **DNS-01 Challenge**: Use certbot manual DNS-01 (or another DNS-01 method); port 80 is not required
- **Transport**: VLESS over WebSocket (path `/ws`) fronted by Caddy
# GFWMass

GFWMass helps create and manage many friendly-looking subdomains and produces a single subscription you can import into a client. This README was simplified to keep only the essentials.

Quick, non-technical steps:

- Provide a domain and a Cloudflare API token.
- Obtain a wildcard TLS certificate for your domain.
- Run `install.sh` and follow the prompts.

For full installation details and advanced options, see the project guide:
https://forum.blackfox.qzz.io/posts/introduction-to-gfwmass/

The original, detailed README has been saved as [README.backup.md](README.backup.md).

License: MIT (see the LICENSE file).
