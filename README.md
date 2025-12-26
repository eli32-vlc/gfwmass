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
4. **Xray/VLESS**: Single VLESS endpoint serving all domains
5. **Subscription**: Base64-encoded link containing all proxy endpoints

### Key Features

- **Wildcard Certificate**: Uses a single wildcard certificate (*.example.com) you provide (certbot DNS-01 recommended)
- **DNS-01 Challenge**: Use certbot manual DNS-01 (or another DNS-01 method); port 80 is not required
- **Renewal**: Renew your cert externally (e.g., re-run certbot manual DNS-01) and reload Caddy
- **Scalable**: Easily support hundreds or thousands of subdomains with a single certificate

## Prerequisites

- Linux server (Ubuntu/Debian recommended)
- Domain name with Cloudflare DNS
- Cloudflare API token with DNS edit permissions
- Python 3.6+
- certbot (for issuing a wildcard cert via DNS-01)
- Root/sudo access for installation

**Note:** You must obtain and provide the wildcard certificate yourself (e.g., certbot manual DNS-01). Caddy is installed from the official repo without DNS provider modules.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/eli32-vlc/gfwmass.git
cd gfwmass
```

### 2. Install Python Dependencies

```bash
pip3 install requests
```

### 3. Create Configuration File

Copy the example configuration and edit it with your details:

```bash
cp config.example.json config.json
nano config.json
```

Edit the following fields:

```json
{
  "domain": "example.com",              // Your domain name
  "origin_ip": "1.2.3.4",               // Your server's IP address
  "email": "admin@example.com",         // Email for SSL certificates
  "xray_port": 10000,                   // Port for Xray to listen on
  "user_id": "your-uuid-here",          // UUID for VLESS (generate with uuidgen)
  "cloudflare": {
    "api_token": "your-token",          // Cloudflare API token
    "zone_id": "your-zone-id"           // Cloudflare zone ID
  }
}
```

#### Getting Cloudflare Credentials

1. **API Token**: 
   - Go to https://dash.cloudflare.com/profile/api-tokens
   - Create token with "Edit DNS" permissions for your zone
   
2. **Zone ID**:
   - Go to your domain's overview page in Cloudflare
   - Scroll down to "API" section on the right sidebar
   - Copy the Zone ID

3. **Generate UUID**:
   ```bash
   uuidgen
   # or
   python3 -c "import uuid; print(uuid.uuid4())"
   ```

## Usage

### Generate Configs Only (Test Mode)

Generate configuration files without deploying to Cloudflare:

```bash
python3 gfwmass.py --generate-only --count 100
```

This creates:
- `Caddyfile` - Caddy reverse proxy configuration
- `xray_config.json` - Xray VLESS configuration
- `domains.txt` - List of all generated domains
- `subscription.txt` - Base64-encoded subscription link
- `subscription_decoded.txt` - Human-readable subscription links

### Full Deployment

Deploy everything (DNS records, install dependencies, configure services):

```bash
sudo python3 gfwmass.py --deploy --count 200
```

This will:
1. Generate 200 subdomains
2. Add all DNS records to Cloudflare
3. Install Caddy, certbot, and Xray
4. Deploy configurations
5. Restart services

### Install Dependencies Only

If you want to install Caddy and Xray separately:

```bash
sudo python3 gfwmass.py --install-only
```

## Command Line Options

```
-c, --config FILE       Configuration file path (default: config.json)
-n, --count NUMBER      Number of subdomains to generate (default: 100)
--generate-only         Generate configs without Cloudflare deployment
--deploy                Deploy to Cloudflare and install services
--install-only          Install dependencies only
```

## Generated Files

### Caddyfile
Caddy configuration handling all domains with a provided wildcard certificate:
```
*.example.com {
  reverse_proxy localhost:10000
  tls /etc/ssl/gfwmass/fullchain.pem /etc/ssl/gfwmass/privkey.pem
  encode gzip
}
```

**Note:** You must issue the wildcard certificate yourself (e.g., `certbot certonly --manual --preferred-challenges dns -d example.com -d '*.example.com'`) and place the files at the paths above before starting Caddy.

### xray_config.json
Xray VLESS configuration:
```json
{
  "inbounds": [{
    "port": 10000,
    "protocol": "vless",
    "settings": {
      "clients": [{"id": "your-uuid"}],
      "decryption": "none"
    }
  }]
}
```

### subscription.txt
Base64-encoded subscription link containing all VLESS endpoints. Import this into your client (v2rayN, Clash, etc.).

## Client Configuration

### 1. Import Subscription

Import the content of `subscription.txt` into your client:
- **v2rayN**: Subscription → Add → Paste URL/content
- **Clash**: Add subscription URL
- **Qv2ray**: Import from file

### 2. Configure Rotation

**Important**: Configure your client to rotate endpoints every few minutes for optimal load distribution:

- **v2rayN**: Enable "Auto switch" with 2-5 minute intervals
- **Clash**: Use load-balance or fallback-auto strategies
- **Custom scripts**: Rotate through the list programmatically

## Monitoring

Check service status:

```bash
# Caddy logs
journalctl -u caddy -f

# Xray logs
journalctl -u xray -f

# Check if services are running
systemctl status caddy
systemctl status xray
```

## Security Considerations

1. **Keep your UUID secret** - This is your authentication credential
2. **Restrict access** - Use firewall rules to limit access to necessary ports
3. **Monitor traffic** - Watch for unusual patterns
4. **Regular updates** - Keep Caddy and Xray updated
5. **Rotate credentials** - Periodically regenerate UUID and redeploy

## Firewall Configuration

Allow necessary ports:

```bash
# Allow HTTPS
ufw allow 443/tcp

# Note: Port 80 is NOT required since we use DNS-01 challenge for certificates
# The wildcard certificate is obtained via Cloudflare DNS API, not HTTP challenge

# Enable firewall
ufw enable
```

## Troubleshooting

### DNS Records Not Propagating
- Check Cloudflare dashboard to verify records were created
- Wait a few minutes for propagation
- Verify zone ID and API token are correct

### Caddy Not Starting
- Check Caddyfile syntax: `caddy validate --config /etc/caddy/Caddyfile`
- Check logs: `journalctl -u caddy -n 50`
- Ensure port 443 is available
- Verify Cloudflare API token has DNS edit permissions

### Xray Connection Failed
- Verify UUID matches in server and client
- Check Xray logs: `journalctl -u xray -n 50`
- Ensure xray_port is not blocked by firewall

### Certificate Issues
- Ensure email is set correctly in config.json
- Verify Cloudflare API token has DNS edit permissions for your zone
- Check Caddy logs for DNS-01 challenge errors: `journalctl -u caddy -n 100`
- The wildcard certificate uses DNS-01 challenge, so port 80 is not required

## Advanced Configuration

### Custom Subdomain Patterns

Edit `gfwmass.py` and modify the `generate_subdomains()` method to customize naming patterns:

```python
prefixes = ['custom', 'prefix', 'list']
```

### Multiple Users

Add multiple UUIDs to xray_config.json:

```json
"clients": [
  {"id": "uuid-1", "level": 0},
  {"id": "uuid-2", "level": 0}
]
```

### Custom Port

Change `xray_port` in config.json and regenerate configs.

## Scaling

For more than 500 domains:
1. Monitor Cloudflare rate limits (1200 requests/5min for free plan)
2. Add delays between DNS record creation
3. Consider multiple origin servers for true load balancing

## Uninstallation

```bash
# Stop services
systemctl stop caddy xray

# Remove packages
apt remove caddy
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ remove

# Remove configs
rm -rf /etc/caddy /usr/local/etc/xray

# Clean up DNS (manual via Cloudflare dashboard or API)
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational and legitimate use only. Users are responsible for complying with all applicable laws and regulations. The authors are not responsible for misuse of this software.

## Support

- Issues: https://github.com/eli32-vlc/gfwmass/issues
- Documentation: https://github.com/eli32-vlc/gfwmass/wiki

## Acknowledgments

- [Cloudflare](https://cloudflare.com) - CDN and DNS service
- [Caddy](https://caddyserver.com) - Modern web server
- [Xray](https://github.com/XTLS/Xray-core) - Proxy platform
