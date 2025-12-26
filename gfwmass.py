#!/usr/bin/env python3

import json
import random
import string
import base64
import uuid
import sys
import os
import subprocess
from typing import List, Dict, Any
import argparse

try:
    import requests
except ImportError:
    print("Error: requests library not found. Please run: pip3 install requests")
    sys.exit(1)


class GFWMass:
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.domains = []
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        if not os.path.exists(config_file):
            print(f"Error: Configuration file '{config_file}' not found.")
            print("Please create a config.json file. See config.example.json for template.")
            sys.exit(1)
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def generate_subdomains(self, count: int = 100) -> List[str]:
        service_prefixes = [
            'cdn', 'api', 'static', 'assets', 'media', 'img', 'images', 'video', 'videos',
            'auth', 'login', 'signin', 'signup', 'register', 'account', 'user', 'profile',
            'app', 'web', 'mobile', 'www', 'm', 'secure', 'ssl', 'portal',
            'gateway', 'edge', 'node', 'cloud', 'data', 'analytics', 'metrics',
            'upload', 'download', 'files', 'docs', 'storage', 'backup',
            'mail', 'smtp', 'imap', 'pop', 'webmail', 'exchange',
            'shop', 'store', 'cart', 'checkout', 'payment', 'billing',
            'support', 'help', 'ticket', 'chat', 'forum', 'community',
            'blog', 'news', 'press', 'info', 'status', 'health', 'monitor',
            'dashboard', 'admin', 'panel', 'console', 'manage', 'control',
            'dev', 'staging', 'test', 'demo', 'preview', 'beta',
            'us', 'eu', 'asia', 'jp', 'uk', 'de', 'fr', 'au', 'ca',
            'east', 'west', 'north', 'south', 'central',
            'lb', 'balancer', 'cache', 'dist', 'distribution', 'content',
            'stream', 'live', 'vod', 'hls', 'rtmp', 'ws', 'wss',
            'git', 'repo', 'registry', 'packages', 'npm', 'maven'
        ]
        
        regions = ['us', 'eu', 'asia', 'east', 'west', 'north', 'south', 'central']
        suffixes = ['srv', 'svc', 'service', 'host', 'server', 'cluster', 'net']
        
        domains = []
        base_domain = self.config['domain']
        
        for i in range(count):
            pattern = random.choice([
                'prefix-hash', 'prefix-number', 'hash-only', 'prefix-region-num',
                'service-suffix', 'multi-prefix', 'numbered-prefix'
            ])
            
            if pattern == 'prefix-hash':
                prefix = random.choice(service_prefixes)
                hash_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            
            elif pattern == 'prefix-number':
                prefix = random.choice(service_prefixes)
                number = random.randint(1, 999)
                subdomain = f"{prefix}{number}.{base_domain}"
            
            elif pattern == 'hash-only':
                hash_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                subdomain = f"{hash_str}.{base_domain}"
            
            elif pattern == 'prefix-region-num':
                prefix = random.choice(service_prefixes)
                region = random.choice(regions)
                number = random.randint(1, 99)
                subdomain = f"{prefix}-{region}-{number:02d}.{base_domain}"
            
            elif pattern == 'service-suffix':
                prefix = random.choice(service_prefixes)
                suffix = random.choice(suffixes)
                subdomain = f"{prefix}-{suffix}.{base_domain}"
            
            elif pattern == 'multi-prefix':
                region = random.choice(regions)
                service = random.choice(service_prefixes)
                subdomain = f"{region}-{service}.{base_domain}"
            
            else:
                prefix = random.choice(service_prefixes)
                number = random.randint(1, 99)
                subdomain = f"{prefix}{number:02d}.{base_domain}"
            
            domains.append(subdomain)
        
        self.domains = domains
        return domains
    
    def add_cloudflare_records(self) -> bool:
        cf_token = self.config['cloudflare']['api_token']
        zone_id = self.config['cloudflare']['zone_id']
        origin_ip = self.config['origin_ip']
        
        headers = {
            'Authorization': f'Bearer {cf_token}',
            'Content-Type': 'application/json'
        }
        
        base_url = f"https://api.cloudflare.com/v4/zones/{zone_id}/dns_records"
        
        success_count = 0
        failed_count = 0
        
        print(f"Adding {len(self.domains)} DNS records to Cloudflare...")
        
        for i, domain in enumerate(self.domains):
            subdomain = domain.split('.')[0]
            
            data = {
                'type': 'A',
                'name': subdomain,
                'content': origin_ip,
                'ttl': 1,  # Auto
                'proxied': True  # Enable Cloudflare proxy
            }
            
            try:
                response = requests.post(base_url, headers=headers, json=data)
                if response.status_code in [200, 201]:
                    success_count += 1
                    if (i + 1) % 10 == 0:
                        print(f"Progress: {i + 1}/{len(self.domains)} records added")
                else:
                    failed_count += 1
                    print(f"Failed to add {domain}: {response.text}")
            except Exception as e:
                failed_count += 1
                print(f"Error adding {domain}: {str(e)}")
        
        print(f"\nCompleted: {success_count} successful, {failed_count} failed")
        return failed_count == 0
    
    def generate_caddy_config(self) -> str:
        email = self.config.get('email', 'admin@example.com')
        xray_port = self.config.get('xray_port', 10000)
        
        config = f"""{{
    email {email}
}}

"""
        
        for domain in self.domains:
            config += f"""
{domain} {{
    reverse_proxy localhost:{xray_port}
    tls {{
        protocols tls1.2 tls1.3
    }}
    encode gzip
}}
"""
        
        return config
    
    def generate_xray_config(self) -> Dict[str, Any]:
        user_id = self.config.get('user_id', str(uuid.uuid4()))
        port = self.config.get('xray_port', 10000)
        
        config = {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "port": port,
                    "protocol": "vless",
                    "settings": {
                        "clients": [
                            {
                                "id": user_id,
                                "level": 0
                            }
                        ],
                        "decryption": "none"
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "none"
                    }
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom",
                    "settings": {}
                }
            ]
        }
        
        return config
    
    def generate_subscription(self) -> str:
        user_id = self.config.get('user_id', str(uuid.uuid4()))
        
        links = []
        for domain in self.domains:
            link = f"vless://{user_id}@{domain}:443?encryption=none&security=tls&type=tcp#{domain}"
            links.append(link)
        
        subscription_content = '\n'.join(links)
        encoded = base64.b64encode(subscription_content.encode()).decode()
        
        return encoded
    
    def save_configs(self):
        caddy_config = self.generate_caddy_config()
        with open('Caddyfile', 'w') as f:
            f.write(caddy_config)
        print("✓ Caddyfile generated")
        
        xray_config = self.generate_xray_config()
        with open('xray_config.json', 'w') as f:
            json.dump(xray_config, f, indent=2)
        print("✓ xray_config.json generated")
        
        with open('domains.txt', 'w') as f:
            f.write('\n'.join(self.domains))
        print("✓ domains.txt generated")
        
        subscription = self.generate_subscription()
        with open('subscription.txt', 'w') as f:
            f.write(subscription)
        print("✓ subscription.txt generated (base64 encoded)")
        
        with open('subscription_decoded.txt', 'w') as f:
            decoded = base64.b64decode(subscription).decode()
            f.write(decoded)
        print("✓ subscription_decoded.txt generated (human readable)")
    
    def install_dependencies(self):
        print("\n=== Installing Dependencies ===\n")
        
        if os.geteuid() != 0:
            print("Warning: Not running as root. You may need sudo privileges.")
        
        print("⚠️  Security Notice:")
        print("This will download and execute installation scripts from:")
        print("  - https://dl.cloudsmith.io (Caddy)")
        print("  - https://github.com/XTLS/Xray-install (Xray)")
        print("")
        
        print("Installing Caddy...")
        caddy_commands = [
            "apt install -y debian-keyring debian-archive-keyring apt-transport-https curl",
            "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg",
            "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list",
            "apt update",
            "apt install -y caddy"
        ]
        
        for cmd in caddy_commands:
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Command failed: {cmd}")
        
        print("\nInstalling Xray...")
        print("Note: Downloading official installation script from GitHub...")
        xray_install_cmd = "bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\" @ install"
        try:
            subprocess.run(xray_install_cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            print("Warning: Xray installation may have failed. Please install manually if needed.")
        
        print("\n✓ Dependencies installation completed")
    
    def deploy_configs(self):
        print("\n=== Deploying Configurations ===\n")
        
        caddy_path = "/etc/caddy/Caddyfile"
        if os.path.exists("Caddyfile"):
            try:
                subprocess.run(f"cp Caddyfile {caddy_path}", shell=True, check=True)
                print(f"✓ Caddyfile deployed to {caddy_path}")
            except subprocess.CalledProcessError:
                print(f"Warning: Failed to copy Caddyfile. You may need to manually copy it to {caddy_path}")
        
        xray_path = "/usr/local/etc/xray/config.json"
        if os.path.exists("xray_config.json"):
            try:
                subprocess.run(f"cp xray_config.json {xray_path}", shell=True, check=True)
                print(f"✓ Xray config deployed to {xray_path}")
            except subprocess.CalledProcessError:
                print(f"Warning: Failed to copy Xray config. You may need to manually copy it to {xray_path}")
        
        print("\n✓ Configuration deployment completed")
    
    def restart_services(self):
        print("\n=== Restarting Services ===\n")
        
        services = ["caddy", "xray"]
        for service in services:
            try:
                subprocess.run(f"systemctl restart {service}", shell=True, check=True)
                print(f"✓ {service} restarted")
            except subprocess.CalledProcessError:
                print(f"Warning: Failed to restart {service}. You may need to do this manually.")
        
        print("\n✓ Services restart completed")


def main():
    parser = argparse.ArgumentParser(
        description='GFWMass - Automated Multi-Domain Proxy System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate domains and configs only (no Cloudflare deployment)
  python3 gfwmass.py --generate-only

  # Full deployment with 200 domains
  python3 gfwmass.py --count 200 --deploy

  # Install dependencies only
  python3 gfwmass.py --install-only

Commands:
  generate-only: Generate configs without deploying to Cloudflare
  deploy: Deploy DNS records to Cloudflare and install services
  install-only: Install dependencies without generating configs
        """
    )
    
    parser.add_argument('-c', '--config', default='config.json',
                       help='Configuration file path (default: config.json)')
    parser.add_argument('-n', '--count', type=int, default=100,
                       help='Number of subdomains to generate (default: 100)')
    parser.add_argument('--generate-only', action='store_true',
                       help='Generate configs only without Cloudflare deployment')
    parser.add_argument('--deploy', action='store_true',
                       help='Deploy to Cloudflare and install services')
    parser.add_argument('--install-only', action='store_true',
                       help='Install dependencies only')
    
    args = parser.parse_args()
    
    if args.install_only:
        gfw = GFWMass(args.config)
        gfw.install_dependencies()
        return
    
    # Initialize
    gfw = GFWMass(args.config)
    
    # Generate subdomains
    print(f"\n=== Generating {args.count} Subdomains ===\n")
    domains = gfw.generate_subdomains(args.count)
    print(f"✓ Generated {len(domains)} subdomains")
    print(f"Examples: {domains[:5]}")
    
    # Save configurations
    print("\n=== Generating Configurations ===\n")
    gfw.save_configs()
    
    if args.deploy:
        # Add to Cloudflare
        print("\n=== Deploying to Cloudflare ===\n")
        success = gfw.add_cloudflare_records()
        
        if success:
            print("\n=== Installing Dependencies ===")
            gfw.install_dependencies()
            
            print("\n=== Deploying Configurations ===")
            gfw.deploy_configs()
            
            print("\n=== Restarting Services ===")
            gfw.restart_services()
            
            print("\n" + "="*50)
            print("✓ Deployment completed successfully!")
            print("="*50)
            print("\nNext steps:")
            print("1. Check subscription.txt for the base64-encoded subscription link")
            print("2. Import the subscription link into your client")
            print("3. Configure client to rotate endpoints every few minutes")
            print("4. Monitor logs: journalctl -u caddy -f")
            print("            journalctl -u xray -f")
    else:
        print("\n" + "="*50)
        print("✓ Configuration generation completed!")
        print("="*50)
        print("\nGenerated files:")
        print("  - Caddyfile")
        print("  - xray_config.json")
        print("  - domains.txt")
        print("  - subscription.txt (base64 encoded)")
        print("  - subscription_decoded.txt (human readable)")
        print("\nTo deploy to Cloudflare, run:")
        print(f"  python3 gfwmass.py --deploy")


if __name__ == '__main__':
    main()
