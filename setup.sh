#!/bin/bash

# youversion to notion sync - quick setup script
# author: DD

echo "=================================================="
echo "YouVersion -> Notion Sync Setup"
echo "=================================================="
echo ""

# check if python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "Python found: $(python3 --version)"

# create virtual environment (optional but recommended)
echo ""
echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# create .env file if it doesnt exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.template .env
    echo "Warning: Please edit .env and add your Notion credentials!"
    echo "   NOTION_TOKEN and NOTION_PAGE_ID are required."
else
    echo ""
    echo ".env file already exists"
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Notion credentials"
echo "2. Run: python test_sync.py (to test)"
echo "3. Run: python youversion_sync_enhanced.py (for real sync)"
echo "4. Set up automation (see README.md)"
echo ""
echo "Need help? Check README.md for detailed instructions."
echo ""
