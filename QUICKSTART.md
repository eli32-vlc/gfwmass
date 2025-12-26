# Quick Start Guide

This guide will help you get GFWMass up and running in minutes.

## Prerequisites Checklist

Before starting, make sure you have:

- [ ] A Linux server (Ubuntu 20.04+ or Debian 11+ recommended)
- [ ] Root/sudo access to the server
- [ ] A domain name (e.g., example.com)
- [ ] Domain DNS managed by Cloudflare
- [ ] Cloudflare API token with DNS edit permissions
- [ ] Python 3.6 or higher installed

## Step-by-Step Setup

### 1. Get Server Ready

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not already installed
sudo apt install -y python3 python3-pip git

# Install uuidgen for generating user ID
sudo apt install -y uuid-runtime
```

### 2. Clone and Install

```bash
# Clone the repository
git clone https://github.com/eli32-vlc/gfwmass.git
cd gfwmass

# Install Python dependencies
pip3 install -r requirements.txt
```

### 3. Get Cloudflare Credentials

#### Get API Token:
1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use the "Edit zone DNS" template
4. Select your domain under "Zone Resources"
5. Click "Continue to summary" → "Create Token"
6. **Copy the token** (you won't see it again!)

#### Get Zone ID:
1. Go to https://dash.cloudflare.com
2. Select your domain
3. Scroll down on the Overview page
4. Find "Zone ID" in the API section (right sidebar)
5. Copy the Zone ID

### 4. Configure GFWMass

```bash
# Copy the example config
cp config.example.json config.json

# Generate a UUID for VLESS
UUID=$(uuidgen)
echo "Your UUID: $UUID"

# Edit the config file
nano config.json
```

Update `config.json` with your details:

```json
{
  "domain": "yourdomain.com",              // ← Your domain
  "origin_ip": "YOUR.SERVER.IP.HERE",      // ← Your server's public IP
  "email": "your@email.com",               // ← Your email (for SSL certs)
  "xray_port": 10000,                      // ← Keep default or change
  "user_id": "paste-uuid-here",            // ← Paste the UUID from above
  "cloudflare": {
    "api_token": "paste-token-here",       // ← Paste Cloudflare API token
    "zone_id": "paste-zone-id-here"        // ← Paste Cloudflare Zone ID
  }
}
```

### 5. Test Configuration (Optional but Recommended)

Before deploying to production, test that everything works:

```bash
# Generate configs without deploying to Cloudflare
python3 gfwmass.py --generate-only --count 5

# Check generated files
ls -lh Caddyfile xray_config.json domains.txt subscription.txt

# View some example domains
cat domains.txt
```

If everything looks good, clean up the test files:

```bash
rm -f Caddyfile xray_config.json domains.txt subscription.txt subscription_decoded.txt
```

### 6. Deploy Everything

Now deploy the full system:

```bash
# Deploy with 100 domains (recommended for start)
sudo python3 gfwmass.py --deploy --count 100
```

This will:
1. Generate 100 realistic subdomains
2. Add all DNS records to Cloudflare
3. Install Caddy and Xray
4. Deploy configurations
5. Start services

The process takes 5-10 minutes depending on your domain count.

### 7. Verify Deployment

```bash
# Check if services are running
sudo systemctl status caddy
sudo systemctl status xray

# Check logs for errors
sudo journalctl -u caddy -n 50
sudo journalctl -u xray -n 50

# Test if Caddy is responding
curl -I https://$(head -1 domains.txt)
```

### 8. Get Your Subscription Link

```bash
# View the subscription content
cat subscription.txt

# Or view human-readable format
cat subscription_decoded.txt | head -10
```

The `subscription.txt` file contains a base64-encoded subscription link with all your proxy endpoints.

### 9. Configure Your Client

#### Option A: v2rayN (Windows/Android)

1. Open v2rayN
2. Go to **Subscriptions** → **Subscription Settings**
3. Add new subscription:
   - Type: Base64
   - URL: Paste content from `subscription.txt` or host it on a web server
4. Click **Update Subscription**
5. All endpoints will appear in your server list

#### Option B: Clash (Windows/macOS/Android)

1. Create a Clash config or use subscription converter
2. Import the VLESS links from `subscription_decoded.txt`
3. Set up load-balancing or fallback rules

#### Option C: Qv2ray (Cross-platform)

1. Open Qv2ray
2. **Subscriptions** → **New**
3. Paste subscription or import from file
4. Update subscription

### 10. Configure Endpoint Rotation

**Important:** For optimal load distribution, configure your client to rotate endpoints:

- **v2rayN**: Enable automatic switching every 2-5 minutes
- **Clash**: Use `load-balance` or `url-test` proxy groups
- **Custom setup**: Rotate through the endpoint list programmatically

## Scaling Up

Once everything is working, you can scale up:

```bash
# Generate and deploy 500 domains
sudo python3 gfwmass.py --deploy --count 500
```

**Note:** Cloudflare free plan has rate limits (1200 requests per 5 minutes). The script handles this automatically, but large deployments will take longer.

## Troubleshooting

### DNS Records Not Created

**Problem:** Cloudflare API returns errors

**Solutions:**
- Verify API token has correct permissions
- Check Zone ID is correct
- Ensure domain is active on Cloudflare
- Check rate limits

### Caddy Won't Start

**Problem:** `systemctl status caddy` shows failed

**Solutions:**
```bash
# Validate Caddyfile syntax
sudo caddy validate --config /etc/caddy/Caddyfile

# Check what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443

# Check detailed logs
sudo journalctl -u caddy -n 100 --no-pager
```

### Xray Connection Failed

**Problem:** Client can't connect

**Solutions:**
- Verify UUID matches in config.json and client
- Check Xray logs: `sudo journalctl -u xray -n 50`
- Ensure firewall allows port 443
- Test if domain resolves: `dig $(head -1 domains.txt)`
- Check if Caddy is proxying: `curl -v https://$(head -1 domains.txt)`

### SSL Certificate Issues

**Problem:** Certificate validation fails

**Solutions:**
- Wait a few minutes for ACME challenge to complete
- Ensure port 80 is accessible (needed for Let's Encrypt)
- Check email in config.json is valid
- View Caddy logs for ACME errors

## Maintenance

### View Logs

```bash
# Real-time Caddy logs
sudo journalctl -u caddy -f

# Real-time Xray logs
sudo journalctl -u xray -f
```

### Restart Services

```bash
sudo systemctl restart caddy
sudo systemctl restart xray
```

### Add More Domains

```bash
# Generate more domains and update
sudo python3 gfwmass.py --deploy --count 200
```

### Update Configuration

```bash
# Edit config
nano config.json

# Regenerate everything
sudo python3 gfwmass.py --deploy --count 100
```

## Security Best Practices

1. **Keep UUID Secret**: Never share your UUID publicly
2. **Use Strong Passwords**: If you add authentication layers
3. **Monitor Traffic**: Watch for unusual patterns
4. **Regular Updates**: Keep Caddy and Xray updated
5. **Firewall Rules**: Only allow necessary ports (80, 443)
6. **Backup Config**: Save your config.json securely

## Next Steps

- Read the full [README.md](README.md) for advanced configuration
- Set up monitoring and alerting
- Configure automatic SSL certificate renewal (Caddy handles this automatically)
- Set up multiple origin servers for true load balancing

## Getting Help

- Issues: https://github.com/eli32-vlc/gfwmass/issues
- Check logs first: `journalctl -u caddy` and `journalctl -u xray`
- Verify config.json is correct
- Test with fewer domains first (5-10) before scaling up

---

**Congratulations!** You now have a distributed, multi-domain proxy system running. 🎉
