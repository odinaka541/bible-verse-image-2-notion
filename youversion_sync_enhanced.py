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
        from urllib.parse import unquote
        from bs4 import BeautifulSoup

        url = "https://www.bible.com/verse-of-the-day"
        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # find the votd image - look for 640x640 images from youversion
        image_url = None
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if '640x640' in src:
                # decode the next.js image proxy url
                decoded = unquote(src)
                # extract the s3 url
                if 'https://s3' in decoded:
                    s3_part = decoded.split('https://s3')[1]
                    image_url = 'https://s3' + s3_part.split('&')[0].split(' ')[0]
                    break

        if not image_url:
            raise Exception("Could not find verse image")

        # find the verse text and citation from the votd card
        citation = "Unknown"
        passage = "Unknown"

        # find all divs and look for the votd container
        for div in soup.find_all('div'):
            classes = div.get('class', [])
            class_str = ' '.join(classes) if classes else ''

            # the main votd card has specific classes
            if 'max-w-[530px]' in class_str and 'shadow-light-2' in class_str:
                text = div.get_text(strip=True)
                if 'Verse of the Day' in text:
                    # find all links - first is verse text, second is citation
                    links = div.find_all('a')
                    for a in links:
                        href = a.get('href', '')
                        link_text = a.get_text(strip=True)

                        if '/bible/compare/' in href:
                            # this is the verse text - clean up all quote types
                            passage = link_text.strip().strip('""\u201c\u201d')
                        elif '/bible/' in href and '(' in link_text:
                            # this is the citation with translation (e.g. "Matthew 7:12 (ESV)")
                            citation = link_text
                            break
                    break

        return {
            'citation': citation,
            'passage': passage,
            'image_url': image_url,
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
        }

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
        add verse image to notion page
        """
        try:
            url = f"{self.base_url}/blocks/{self.page_id}/children"

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

            print("Successfully uploaded to Notion!")
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
