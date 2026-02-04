
#!/usr/bin/env python3
"""
notion block explorer
lists all blocks in your page so you can find the right block id to target
"""

import os
import requests
from dotenv import load_dotenv


def get_all_blocks(page_id, token, indent=0):
    """recursively get all blocks and their children"""

    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    data = response.json()
    blocks = data.get('results', [])

    for i, block in enumerate(blocks, 1):
        block_type = block.get('type')
        block_id = block.get('id')
        has_children = block.get('has_children', False)

        # get block content/text
        content = get_block_text(block)

        # print block info with indentation
        prefix = "  " * indent
        print(f"{prefix}[{i}] {block_type.upper()}")
        print(f"{prefix}    ID: {block_id}")
        if content:
            print(f"{prefix}    Content: {content[:60]}...")
        print(f"{prefix}    Has children: {has_children}")
        print()

        # recursively get children
        if has_children:
            get_all_blocks(block_id, token, indent + 1)


def get_block_text(block):
    """extract text content from a block"""
    block_type = block.get('type')
    block_data = block.get(block_type, {})

    # most blocks have rich_text
    if 'rich_text' in block_data:
        texts = block_data['rich_text']
        return ''.join([t.get('plain_text', '') for t in texts])

    return None


def main():
    print("=" * 60)
    print("Notion Block Explorer")
    print("=" * 60)

    load_dotenv()

    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    PAGE_ID = os.getenv('NOTION_PAGE_ID')

    if not NOTION_TOKEN or not PAGE_ID:
        print("Error: Missing credentials in .env file")
        return

    print("\nFetching all blocks from your page...\n")

    get_all_blocks(PAGE_ID, NOTION_TOKEN)

    print("=" * 60)
    print("Instructions:")
    print("=" * 60)
    print("\n1. Find the block where you want verses to appear")
    print("2. Copy its block ID")
    print("3. Update your .env file:")
    print("   TARGET_BLOCK_ID=paste_the_id_here")
    print("\n4. The verses will appear INSIDE that block")
    print("   (if it's a toggle/heading) or AFTER it")
    print()


if __name__ == "__main__":
    main()
