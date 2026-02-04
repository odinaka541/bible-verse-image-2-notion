"""
youversion verse of the day -> notion sync (enhanced version)
uses multiple strategies to reliably fetch the verse image:
1. life.church official image repository
2. unofficial youversion api
3. web scraping fallback

author: DD
"""

import os
import requests
from datetime import datetime, timezone
from typing import Dict, Optional
import json
from pathlib import Path


class EnhancedYouVersionFetcher:
    """
    multi-strategy fetcher for youversion verse of the day
    implements fallback mechanisms for maximum reliability
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # life.church cdn base url
        self.lifechurch_cdn = "https://d347bo4ltvvnaz.cloudfront.net/images/"

    def get_verse_of_the_day(self) -> Optional[Dict[str, str]]:
        """
        fetch today's verse using multiple strategies

        returns:
            dict with verse data or none if all strategies fail
        """
        strategies = [
            self._strategy_lifechurch_image,
            self._strategy_bible_com_api,
            self._strategy_unofficial_api,
        ]

        for strategy in strategies:
            try:
                result = strategy()
                if result and result.get('image_url'):
                    print(f"Successfully fetched using: {strategy.__name__}")
                    return result
            except Exception as e:
                print(f"Warning: {strategy.__name__} failed: {e}")
                continue

        print("Error: All strategies failed to fetch verse")
        return None

    def _strategy_lifechurch_image(self) -> Dict[str, str]:
        """
        strategy 1: use life.church's pre-published images
        most reliable but requires date-based url construction
        """
        today = datetime.now(timezone.utc)

        # life.church publishes images in format: YV_VOTD2025_Month_DDFormat.jpg
        # format can be square or vertical
        month_name = today.strftime('%B')
        day = today.strftime('%d')
        year = today.year

        # try both square and vertical formats
        for format_type in ['Square', 'Vertical']:
            image_filename = f"YV_VOTD{year}_{month_name}_{day}{format_type}.jpg"
            image_url = f"{self.lifechurch_cdn}{image_filename}"

            # check if image exists
            response = self.session.head(image_url)
            if response.status_code == 200:
                # get verse text from bible.com
                verse_data = self._get_verse_text_from_bible_com()
                verse_data['image_url'] = image_url
                return verse_data

        raise Exception("Life.Church image not found for today")

    def _strategy_bible_com_api(self) -> Dict[str, str]:
        """
        strategy 2: scrape bible.com/verse-of-the-day
        """
        url = "https://www.bible.com/verse-of-the-day"
        response = self.session.get(url)
        response.raise_for_status()

        # parse with beautifulsoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # find the verse data (structure may vary)
        # look for json-ld structured data
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            data = json.loads(json_ld.string)
            # extract verse info from structured data
            pass

        # alternative: look for specific elements
        verse_elem = soup.find('span', {'data-usfm': True})
        if verse_elem:
            citation = verse_elem.get('data-usfm')
            passage = verse_elem.text.strip()

            # find image
            img_elem = soup.find('img', class_='verse-image') or soup.find('img', alt='Verse of the Day')
            image_url = img_elem.get('src') if img_elem else None

            if image_url:
                return {
                    'citation': citation,
                    'passage': passage,
                    'image_url': image_url,
                    'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
                }

        raise Exception("Could not parse bible.com page")

    def _strategy_unofficial_api(self) -> Dict[str, str]:
        """
        strategy 3: use unofficial youversion api endpoints
        """
        # there are several community-built apis
        apis = [
            "https://beta.ourmanna.com/api/v1/get?format=json&order=daily",
            # add more api endpoints as needed
        ]

        for api_url in apis:
            try:
                response = self.session.get(api_url)
                data = response.json()

                # parse based on api structure
                if 'verse' in data:
                    return {
                        'citation': data['verse'].get('details', {}).get('reference', 'Unknown'),
                        'passage': data['verse'].get('details', {}).get('text', 'Unknown'),
                        'image_url': None,  # this api doesnt provide images
                        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    }
            except:
                continue

        raise Exception("No unofficial API succeeded")

    def _get_verse_text_from_bible_com(self) -> Dict[str, str]:
        """helper to get verse text from bible.com"""
        url = "https://www.bible.com/verse-of-the-day"
        response = self.session.get(url)

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # extract citation and passage
        citation = "Unknown"
        passage = "Unknown"

        # try to find verse reference
        ref_elem = soup.find('span', class_='verses-reference') or soup.find('p', class_='heading')
        if ref_elem:
            citation = ref_elem.text.strip()

        # try to find passage text
        passage_elem = soup.find('span', class_='verse-text') or soup.find('p', class_='content')
        if passage_elem:
            passage = passage_elem.text.strip()

        return {
            'citation': citation,
            'passage': passage,
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
        }


class NotionUploader:
    """simplified notion uploader with better error handling"""

    def __init__(self, api_token: str, page_id: str):
        self.api_token = api_token
        self.page_id = page_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def add_verse_with_image(self, citation: str, passage: str, image_url: str) -> bool:
        """
        add verse block with image to notion page
        """
        try:
            url = f"{self.base_url}/blocks/{self.page_id}/children"

            today = datetime.now(timezone.utc).strftime('%B %d, %Y')

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
                                "text": {"content": f"{today}"}
                            }]
                        }
                    },
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"{citation}\n\n{passage}"
                                    }
                                }
                            ],
                            "color": "blue_background"
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

            print(f"Successfully uploaded to Notion!")
            return True

        except requests.exceptions.HTTPError as e:
            print(f"Notion API Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"Upload failed: {e}")
            return False


def main():
    """main execution"""
    print("=" * 50)
    print("YouVersion -> Notion Sync")
    print("=" * 50)

    # load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')

    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        print("Error: Missing configuration!")
        print("Please create a .env file with NOTION_TOKEN and NOTION_PAGE_ID")
        return 1

    # fetch verse
    fetcher = EnhancedYouVersionFetcher()
    verse_data = fetcher.get_verse_of_the_day()

    if not verse_data:
        print("Error: Could not fetch verse of the day")
        return 1

    print(f"\nVerse: {verse_data['citation']}")
    print(f"Text: {verse_data['passage'][:100]}...")
    print(f"Image: {verse_data['image_url']}")

    # upload to notion
    uploader = NotionUploader(NOTION_TOKEN, NOTION_PAGE_ID)
    success = uploader.add_verse_with_image(
        verse_data['citation'],
        verse_data['passage'],
        verse_data['image_url']
    )

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
