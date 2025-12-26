#!/bin/bash
# Quick install script for GFWMass

set -e

echo "================================"
echo "GFWMass Quick Install Script"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: Please run as root (use sudo)"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    apt update
    apt install -y python3 python3-pip
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check if config exists
if [ ! -f "config.json" ]; then
    echo ""
    echo "Configuration file not found!"
    echo "Please create config.json from config.example.json:"
    echo "  cp config.example.json config.json"
    echo "  nano config.json"
    echo ""
    echo "Then run: python3 gfwmass.py --deploy"
    exit 1
fi

# Make script executable
if [ -f "gfwmass.py" ]; then
    chmod +x gfwmass.py
else
    echo -e "${RED}Warning: gfwmass.py not found${NC}"
fi

echo ""
echo "================================"
echo "Installation complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your settings"
echo "2. Run: python3 gfwmass.py --generate-only (to test)"
echo "3. Run: python3 gfwmass.py --deploy (to deploy)"
echo ""
