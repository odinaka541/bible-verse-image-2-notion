#!/usr/bin/env python3
"""
simple wrapper script to run the sync with better ux
handles common errors gracefully
"""

import sys
import os
from pathlib import Path


def check_dependencies():
    """check if required packages are installed"""
    required = ['requests', 'beautifulsoup4', 'python-dotenv']
    missing = []

    for package in required:
        try:
            pkg_name = package.replace('-', '_')
            if pkg_name == 'beautifulsoup4':
                pkg_name = 'bs4'
            __import__(pkg_name)
        except ImportError:
            missing.append(package)

    if missing:
        print("Error: Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nRun: pip install -r requirements.txt")
        return False

    return True


def check_env_file():
    """check if .env file exists and has required variables"""
    env_path = Path('.env')

    if not env_path.exists():
        print("Error: .env file not found!")
        print("\nCreate one by:")
        print("  cp .env.template .env")
        print("  # Then edit .env with your credentials")
        return False

    # check if variables are set
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv('NOTION_TOKEN')
    page_id = os.getenv('NOTION_PAGE_ID')

    if not token or not page_id:
        print("Error: Missing configuration in .env file!")
        print("\nPlease set:")
        print("  NOTION_TOKEN=your_token_here")
        print("  NOTION_PAGE_ID=your_page_id_here")
        return False

    if token == 'secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx':
        print("Error: Please update NOTION_TOKEN in .env file")
        print("   with your actual Notion integration token")
        return False

    if page_id == 'your_page_id_here':
        print("Error: Please update NOTION_PAGE_ID in .env file")
        print("   with your actual Notion page ID")
        return False

    return True


def main():
    """main execution"""
    print("Starting YouVersion -> Notion sync...\n")

    # pre-flight checks
    if not check_dependencies():
        return 1

    if not check_env_file():
        return 1

    # import and run the actual sync
    try:
        from youversion_sync_enhanced import main as sync_main
        return sync_main()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("\nFor debugging, run: python test_sync.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
