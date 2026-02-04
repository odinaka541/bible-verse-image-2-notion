"""
youversion -> notion sync with block targeting
enhanced version that can append to specific sections/blocks
"""

import os
import requests
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv


class NotionBlockUploader:
    """upload to specific blocks in notion"""

    def __init__(self, api_token: str, target_id: str):
        """
        initialize uploader

        args:
            api_token: notion integration token
            target_id: either page id or block id to append to
        """
        self.api_token = api_token
        self.target_id = target_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def add_image(self, image_url: str) -> bool:
        """
        add just the image to the target location
        """
        try:
            url = f"{self.base_url}/blocks/{self.target_id}/children"

            data = {
                "children": [
                    {
                        "object": "block",
                        "type": "image",
                        "image": {
                            "type": "external",
                            "external": {"url": image_url}
                        }
                    }
                ]
            }

            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()

            print(f"Successfully uploaded to: {self.target_id}")
            return True

        except requests.exceptions.HTTPError as e:
            print(f"Notion API Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"Upload failed: {e}")
            return False


# import the fetcher from the enhanced script
from youversion_sync_enhanced import EnhancedYouVersionFetcher


def main():
    """main execution with block targeting"""
    print("=" * 50)
    print("YouVersion -> Notion Sync (Block Targeting)")
    print("=" * 50)

    load_dotenv()

    # get credentials
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    PAGE_ID = os.getenv('NOTION_PAGE_ID')
    TARGET_BLOCK_ID = os.getenv('TARGET_BLOCK_ID')

    if not NOTION_TOKEN:
        print("Error: NOTION_TOKEN missing in .env")
        return 1

    if not PAGE_ID:
        print("Error: NOTION_PAGE_ID missing in .env")
        return 1

    # determine target
    if TARGET_BLOCK_ID:
        print(f"Target: Specific block ({TARGET_BLOCK_ID})")
        target_id = TARGET_BLOCK_ID
    else:
        print(f"Target: Page root ({PAGE_ID})")
        target_id = PAGE_ID

    # fetch verse
    print("\nFetching verse of the day...")
    fetcher = EnhancedYouVersionFetcher()
    verse_data = fetcher.get_verse_of_the_day()

    if not verse_data:
        print("Error: Could not fetch verse")
        return 1

    print(f"Found: {verse_data['citation']}")
    print(f"Image: {verse_data['image_url']}")

    # upload to notion
    print("\nUploading to Notion...")
    uploader = NotionBlockUploader(NOTION_TOKEN, target_id)
    success = uploader.add_image(verse_data['image_url'])

    if success:
        print("\nSync completed successfully!")
    else:
        print("\nSync failed!")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
