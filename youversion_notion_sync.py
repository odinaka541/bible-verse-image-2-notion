"""
youversion verse of the day -> notion sync
a system that fetches the daily bible verse image from youversion
and displays it in a notion page.

author: DD
"""

import os
import requests
from datetime import datetime, timezone
from typing import Dict, Optional
import json
from pathlib import Path


class YouVersionScraper:
    """handles fetching the verse of the day from youversion"""

    BASE_URL = "https://www.bible.com"
    VOTD_ENDPOINT = "/verse-of-the-day"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_verse_of_the_day(self) -> Dict[str, str]:
        """
        fetch today's verse of the day

        returns:
            dict with 'citation', 'passage', and 'image_url'
        """
        try:
            response = self.session.get(f"{self.BASE_URL}{self.VOTD_ENDPOINT}")
            response.raise_for_status()

            # parse the html to extract verse information
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, 'html.parser')

            # extract verse citation and passage
            citation_elem = soup.find('p', class_='text-gray-25')
            passage_elem = soup.find('p', class_='text-xl')

            # extract image url - youversion serves different images
            image_elem = soup.find('img', class_='verse-image')

            citation = citation_elem.text.strip() if citation_elem else "Unknown"
            passage = passage_elem.text.strip() if passage_elem else "Unknown"
            image_url = image_elem.get('src') if image_elem else None

            return {
                'citation': citation,
                'passage': passage,
                'image_url': image_url,
                'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"Error fetching verse: {e}")
            return self._get_fallback_verse()

    def _get_fallback_verse(self) -> Dict[str, str]:
        """fallback to using the unofficial api"""
        try:
            # using the unofficial youversion api
            api_url = "https://developers.youversionapi.com/1.0/verse_of_the_day"
            response = self.session.get(api_url)
            data = response.json()

            return {
                'citation': data.get('reference', 'Unknown'),
                'passage': data.get('text', 'Unknown'),
                'image_url': data.get('image', {}).get('url'),
                'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
            }
        except Exception as e:
            print(f"Fallback also failed: {e}")
            return None


class NotionIntegration:
    """handles notion api interactions"""

    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_token: str, page_id: str):
        """
        initialize notion integration

        args:
            api_token: notion integration token
            page_id: target notion page id
        """
        self.api_token = api_token
        self.page_id = page_id
        self.base_url = "https://api.notion.com/v1"

        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION
        }

    def upload_image_to_notion(self, image_url: str) -> bool:
        """
        add an image block to a notion page

        args:
            image_url: url of the image to add

        returns:
            true if successful, false otherwise
        """
        try:
            # notion api endpoint for appending blocks
            url = f"{self.base_url}/blocks/{self.page_id}/children"

            # create the image block
            data = {
                "children": [
                    {
                        "object": "block",
                        "type": "image",
                        "image": {
                            "type": "external",
                            "external": {
                                "url": image_url
                            }
                        }
                    }
                ]
            }

            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()

            print(f"Image uploaded to Notion successfully!")
            return True

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"Error uploading to Notion: {e}")
            return False

    def add_verse_block(self, citation: str, passage: str, image_url: str) -> bool:
        """
        add a complete verse block with heading, text, and image

        args:
            citation: verse citation (e.g., "John 3:16")
            passage: the verse text
            image_url: url of the verse image

        returns:
            true if successful, false otherwise
        """
        try:
            url = f"{self.base_url}/blocks/{self.page_id}/children"

            # get today's date for the heading
            today = datetime.now(timezone.utc).strftime('%B %d, %Y')

            # create a rich block structure
            data = {
                "children": [
                    {
                        "object": "block",
                        "type": "divider",
                        "divider": {}
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": f"Verse of the Day - {today}"}
                            }]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": citation}
                            }]
                        }
                    },
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": passage}
                            }]
                        }
                    },
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

            print(f"Verse block added to Notion successfully!")
            return True

        except Exception as e:
            print(f"Error adding verse block: {e}")
            return False

    def clear_page_content(self) -> bool:
        """
        clear all blocks from the page (optional - for daily refresh)

        returns:
            true if successful, false otherwise
        """
        try:
            # get all block children
            url = f"{self.base_url}/blocks/{self.page_id}/children"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            blocks = response.json().get('results', [])

            # delete each block
            for block in blocks:
                block_id = block['id']
                delete_url = f"{self.base_url}/blocks/{block_id}"
                requests.delete(delete_url, headers=self.headers)

            print(f"Page content cleared!")
            return True

        except Exception as e:
            print(f"Error clearing page: {e}")
            return False


class VerseSyncManager:
    """orchestrates the sync between youversion and notion"""

    def __init__(self, notion_token: str, notion_page_id: str, clear_daily: bool = False):
        """
        initialize the sync manager

        args:
            notion_token: notion integration token
            notion_page_id: target notion page id
            clear_daily: whether to clear the page daily before adding new verse
        """
        self.scraper = YouVersionScraper()
        self.notion = NotionIntegration(notion_token, notion_page_id)
        self.clear_daily = clear_daily

    def sync(self) -> bool:
        """
        execute the sync operation

        returns:
            true if successful, false otherwise
        """
        print("Starting YouVersion -> Notion sync...")

        # fetch verse of the day
        verse_data = self.scraper.get_verse_of_the_day()

        if not verse_data or not verse_data.get('image_url'):
            print("Failed to fetch verse data")
            return False

        print(f"Retrieved: {verse_data['citation']}")
        print(f"Passage: {verse_data['passage'][:50]}...")

        # clear page if needed
        if self.clear_daily:
            self.notion.clear_page_content()

        # add verse block to notion
        success = self.notion.add_verse_block(
            citation=verse_data['citation'],
            passage=verse_data['passage'],
            image_url=verse_data['image_url']
        )

        if success:
            print("Sync completed successfully!")
        else:
            print("Sync failed!")

        return success


def main():
    """main entry point"""

    # configuration - these should be environment variables
    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
    CLEAR_DAILY = os.getenv('CLEAR_DAILY', 'false').lower() == 'true'

    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        print("Error: Missing environment variables!")
        print("Please set NOTION_TOKEN and NOTION_PAGE_ID")
        return 1

    # execute sync
    manager = VerseSyncManager(NOTION_TOKEN, NOTION_PAGE_ID, CLEAR_DAILY)
    success = manager.sync()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
