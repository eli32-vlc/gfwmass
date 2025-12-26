#!/bin/bash
# Example usage script for GFWMass
# This demonstrates the typical workflow

set -e

echo "==========================================="
echo "  GFWMass - Example Usage Demo"
echo "==========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if config exists
if [ ! -f "config.json" ]; then
    echo -e "${RED}Error: config.json not found${NC}"
    echo ""
    echo "Please create config.json first:"
    echo "  cp config.example.json config.json"
    echo "  nano config.json"
    echo ""
    exit 1
fi

# Parse command line arguments
MODE=${1:-demo}

case $MODE in
    demo)
        echo -e "${YELLOW}Running in DEMO mode (no Cloudflare deployment)${NC}"
        echo ""
        echo "This will:"
        echo "  1. Generate 10 test subdomains"
        echo "  2. Create configuration files"
        echo "  3. Show examples (no actual deployment)"
        echo ""
        
        # Generate configs only
        python3 gfwmass.py --generate-only --count 10
        
        echo ""
        echo -e "${GREEN}Demo completed!${NC}"
        echo ""
        echo "Generated files:"
        ls -lh Caddyfile xray_config.json domains.txt subscription.txt
        echo ""
        echo "Example domains:"
        head -5 domains.txt
        echo ""
        echo "To deploy for real, run: ./examples.sh deploy"
        ;;
    
    deploy)
        echo -e "${YELLOW}Running in DEPLOY mode${NC}"
        echo ""
        echo "This will:"
        echo "  1. Generate 100 subdomains"
        echo "  2. Add DNS records to Cloudflare"
        echo "  3. Install and configure services"
        echo ""
        
        read -p "Are you sure? This will make real changes. (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Aborted."
            exit 1
        fi
        
        # Check if running as root
        if [ "$EUID" -ne 0 ]; then 
            echo -e "${RED}Error: Please run as root (use sudo)${NC}"
            exit 1
        fi
        
        # Full deployment
        python3 gfwmass.py --deploy --count 100
        
        echo ""
        echo -e "${GREEN}Deployment completed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Check services: systemctl status caddy xray"
        echo "  2. View logs: journalctl -u caddy -f"
        echo "  3. Get subscription: cat subscription.txt"
        ;;
    
    test)
        echo -e "${YELLOW}Running tests${NC}"
        echo ""
        
        # Test 1: Config validation
        echo "Test 1: Validating configuration..."
        if python3 -c "import json; json.load(open('config.json'))"; then
            echo -e "${GREEN}✓ config.json is valid JSON${NC}"
        else
            echo -e "${RED}✗ config.json is invalid${NC}"
            exit 1
        fi
        
        # Test 2: Generate small batch
        echo ""
        echo "Test 2: Generating 5 test domains..."
        python3 gfwmass.py --generate-only --count 5 > /dev/null
        if [ -f "domains.txt" ]; then
            echo -e "${GREEN}✓ Domain generation successful${NC}"
            echo "Generated domains:"
            cat domains.txt
        else
            echo -e "${RED}✗ Domain generation failed${NC}"
            exit 1
        fi
        
        # Test 3: Validate generated configs
        echo ""
        echo "Test 3: Validating generated Caddyfile..."
        if [ -f "Caddyfile" ]; then
            echo -e "${GREEN}✓ Caddyfile generated${NC}"
        else
            echo -e "${RED}✗ Caddyfile not generated${NC}"
            exit 1
        fi
        
        echo ""
        echo "Test 4: Validating Xray config..."
        if python3 -c "import json; json.load(open('xray_config.json'))"; then
            echo -e "${GREEN}✓ xray_config.json is valid${NC}"
        else
            echo -e "${RED}✗ xray_config.json is invalid${NC}"
            exit 1
        fi
        
        echo ""
        echo -e "${GREEN}All tests passed!${NC}"
        
        # Cleanup test files
        rm -f Caddyfile xray_config.json domains.txt subscription.txt subscription_decoded.txt
        ;;
    
    clean)
        echo -e "${YELLOW}Cleaning up generated files${NC}"
        rm -f Caddyfile xray_config.json domains.txt subscription.txt subscription_decoded.txt
        echo -e "${GREEN}Cleanup completed${NC}"
        ;;
    
    *)
        echo "Usage: $0 [mode]"
        echo ""
        echo "Modes:"
        echo "  demo    - Generate configs without deployment (default)"
        echo "  deploy  - Full deployment to Cloudflare (requires sudo)"
        echo "  test    - Run validation tests"
        echo "  clean   - Remove generated files"
        echo ""
        echo "Examples:"
        echo "  $0 demo          # Safe test run"
        echo "  sudo $0 deploy   # Full deployment"
        echo "  $0 test          # Run tests"
        echo "  $0 clean         # Cleanup"
        exit 1
        ;;
esac
