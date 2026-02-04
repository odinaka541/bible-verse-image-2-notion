#!/usr/bin/env python3
"""
setup devotional section
creates a dedicated section on your notion page for verses
"""

import os
import requests
from dotenv import load_dotenv


def create_devotional_section(page_id, token):
    """create a dedicated section with toggle for daily verses"""

    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # create the structure
    data = {
        "children": [
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Daily Devotionals"}
                    }],
                    "color": "blue"
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "Automatic daily verses from YouVersion Bible"
                        }
                    }],
                    "color": "gray"
                }
            },
            {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Current Month"}
                    }],
                    "color": "default"
                }
            }
        ]
    }

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        results = response.json().get('results', [])

        # find the toggle block
        toggle_block = None
        for block in results:
            if block['type'] == 'toggle':
                toggle_block = block
                break

        if toggle_block:
            toggle_id = toggle_block['id']
            return toggle_id

    return None


def main():
    print("=" * 60)
    print("Setup Devotional Section")
    print("=" * 60)

    load_dotenv()

    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    PAGE_ID = os.getenv('NOTION_PAGE_ID')

    if not NOTION_TOKEN or not PAGE_ID:
        print("Error: Missing credentials in .env")
        return 1

    print("\nCreating devotional section on your page...")
    print("This will add:")
    print("  - Heading: 'Daily Devotionals'")
    print("  - Description text")
    print("  - Collapsible toggle for verses")
    print()

    proceed = input("Continue? (y/n): ")

    if proceed.lower() != 'y':
        print("Cancelled.")
        return 0

    toggle_id = create_devotional_section(PAGE_ID, NOTION_TOKEN)

    if toggle_id:
        print("\nSection created successfully!")
        print(f"\nToggle Block ID: {toggle_id}")
        print("\nNext steps:")
        print("1. Add this to your .env file:")
        print(f"   TARGET_BLOCK_ID={toggle_id}")
        print()
        print("2. Run the sync:")
        print("   python youversion_sync_targeted.py")
        print()
        print("All future verses will appear inside this toggle!")

        # update .env file
        update = input("\nAutomatically update .env? (y/n): ")
        if update.lower() == 'y':
            with open('.env', 'a') as f:
                f.write(f"\nTARGET_BLOCK_ID={toggle_id}\n")
            print(".env updated!")
    else:
        print("Failed to create section")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
