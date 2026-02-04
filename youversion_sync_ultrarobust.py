"""
youversion verse of the day -> notion sync (ultra-robust version)
multiple strategies with extensive debugging and fallbacks
"""

import os
import re
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import json
from urllib.parse import unquote


class UltraRobustYouVersionFetcher:
    """
    enhanced fetcher with better error handling and more strategies
    """

    def __init__(self, debug=True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.debug = debug
        self.lifechurch_cdn = "https://d347bo4ltvvnaz.cloudfront.net/images/"

    def log(self, message):
        """debug logging"""
        if self.debug:
            print(f"[debug] {message}")

    def get_verse_of_the_day(self) -> Optional[Dict[str, str]]:
        """
        fetch today's verse using multiple strategies
        """
        strategies = [
            self._strategy_bible_com_scrape,
            self._strategy_ourmanna_api,
            self._strategy_lifechurch_preview,
            self._strategy_lifechurch_image,
            self._strategy_fallback_verse,
        ]

        for strategy in strategies:
            strategy_name = strategy.__name__.replace('_strategy_', '')
            self.log(f"Trying strategy: {strategy_name}")

            try:
                result = strategy()
                if result and self._validate_verse_data(result):
                    print(f"Successfully fetched using: {strategy_name}")
                    return result
                else:
                    self.log(f"Strategy {strategy_name} returned invalid data")
            except Exception as e:
                self.log(f"Strategy {strategy_name} failed: {e}")
                continue

        print("Error: All strategies failed to fetch verse")
        return None

    def _validate_verse_data(self, data: Dict) -> bool:
        """validate that verse data has an image"""
        if not data:
            return False

        # we only need an image url
        if not data.get('image_url'):
            self.log("Missing image_url")
            return False

        return True

    def _strategy_bible_com_scrape(self) -> Dict[str, str]:
        """
        strategy 1: scrape bible.com with improved parsing
        extracts image from next.js image proxy urls
        """
        url = "https://www.bible.com/verse-of-the-day"

        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        from bs4 import BeautifulSoup
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

        for div in soup.find_all('div'):
            classes = div.get('class', [])
            class_str = ' '.join(classes) if classes else ''

            if 'max-w-[530px]' in class_str and 'shadow-light-2' in class_str:
                text = div.get_text(strip=True)
                if 'Verse of the Day' in text:
                    links = div.find_all('a')
                    for a in links:
                        href = a.get('href', '')
                        link_text = a.get_text(strip=True)

                        if '/bible/compare/' in href:
                            passage = link_text.strip().strip('""\u201c\u201d')
                        elif '/bible/' in href and '(' in link_text:
                            citation = link_text
                            break
                    break

        return {
            'citation': citation,
            'passage': passage,
            'image_url': image_url,
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
        }

    def _strategy_ourmanna_api(self) -> Dict[str, str]:
        """
        strategy 2: ourmanna api (reliable for verse text)
        then tries to get life.church image separately
        """
        url = "https://beta.ourmanna.com/api/v1/get?format=json&order=daily"

        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        verse_data = data.get('verse', {}).get('details', {})

        citation = verse_data.get('reference', '')
        passage = verse_data.get('text', '')

        if not citation or not passage:
            raise Exception("OurManna API returned incomplete data")

        # try to get image from life.church
        image_url = self._get_lifechurch_image_for_today()

        if not image_url:
            raise Exception("No image available for ourmanna verse")

        return {
            'citation': citation,
            'passage': passage,
            'image_url': image_url,
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
        }

    def _strategy_lifechurch_preview(self) -> Dict[str, str]:
        """
        strategy 3: try life.church with preview images folder
        """
        today = datetime.now(timezone.utc)
        month_name = today.strftime('%B')
        day = today.strftime('%d')
        year = today.year

        for format_type in ['Square', 'Vertical']:
            # try with preview prefix
            image_filename = f"preview/YV_VOTD{year}_{month_name}_{day}{format_type}.jpg"
            image_url = f"{self.lifechurch_cdn}{image_filename}"

            self.log(f"Checking: {image_url}")

            response = self.session.head(image_url, timeout=5)
            if response.status_code == 200:
                verse_text = self._get_verse_text_from_ourmanna()
                if verse_text:
                    verse_text['image_url'] = image_url
                    return verse_text

        raise Exception("Life.Church preview images not found")

    def _strategy_lifechurch_image(self) -> Dict[str, str]:
        """
        strategy 4: original life.church strategy
        """
        today = datetime.now(timezone.utc)
        month_name = today.strftime('%B')
        day = today.strftime('%d')
        year = today.year

        for format_type in ['Square', 'Vertical']:
            image_filename = f"YV_VOTD{year}_{month_name}_{day}{format_type}.jpg"
            image_url = f"{self.lifechurch_cdn}{image_filename}"

            response = self.session.head(image_url, timeout=5)
            if response.status_code == 200:
                verse_data = self._get_verse_text_from_ourmanna()
                if verse_data:
                    verse_data['image_url'] = image_url
                    return verse_data

        raise Exception("Life.Church image not found")

    def _strategy_fallback_verse(self) -> Dict[str, str]:
        """
        strategy 5: fallback with any available image
        tries yesterday/tomorrow images as backup
        """
        self.log("Using fallback strategy")

        verse_data = self._get_verse_text_from_ourmanna()

        if not verse_data:
            verse_data = {
                'citation': 'Jeremiah 29:11 (NIV)',
                'passage': 'For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.',
                'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
            }

        # try to get any life.church image
        image_url = self._get_any_lifechurch_image()
        if image_url:
            verse_data['image_url'] = image_url
            return verse_data

        raise Exception("No fallback image available")

    def _get_lifechurch_image_for_today(self) -> Optional[str]:
        """helper to get life.church image for today"""
        today = datetime.now(timezone.utc)
        month_name = today.strftime('%B')
        day = today.strftime('%d')
        year = today.year

        for format_type in ['Square', 'Vertical']:
            for prefix in ['', 'preview/']:
                image_filename = f"{prefix}YV_VOTD{year}_{month_name}_{day}{format_type}.jpg"
                image_url = f"{self.lifechurch_cdn}{image_filename}"

                try:
                    response = self.session.head(image_url, timeout=3)
                    if response.status_code == 200:
                        return image_url
                except:
                    continue

        return None

    def _get_any_lifechurch_image(self) -> Optional[str]:
        """get any available life.church image as fallback"""
        # try yesterday and tomorrow as fallback
        for days_offset in [0, -1, 1, -2, 2]:
            date = datetime.now(timezone.utc) + timedelta(days=days_offset)
            month_name = date.strftime('%B')
            day = date.strftime('%d')
            year = date.year

            for format_type in ['Square', 'Vertical']:
                image_filename = f"YV_VOTD{year}_{month_name}_{day}{format_type}.jpg"
                image_url = f"{self.lifechurch_cdn}{image_filename}"

                try:
                    response = self.session.head(image_url, timeout=3)
                    if response.status_code == 200:
                        self.log(f"Using {days_offset} day offset image")
                        return image_url
                except:
                    continue

        return None

    def _get_verse_text_from_ourmanna(self) -> Optional[Dict[str, str]]:
        """helper to get verse text from ourmanna api"""
        try:
            url = "https://beta.ourmanna.com/api/v1/get?format=json&order=daily"
            response = self.session.get(url, timeout=5)
            data = response.json()

            verse_data = data.get('verse', {}).get('details', {})
            citation = verse_data.get('reference', '')
            passage = verse_data.get('text', '')

            if citation and passage:
                return {
                    'citation': citation,
                    'passage': passage,
                    'date': datetime.now(timezone.utc).strftime('%Y-%m-%d')
                }
        except:
            pass

        return None


class NotionUploader:
    """notion uploader - image only"""

    def __init__(self, api_token: str, page_id: str):
        self.api_token = api_token
        self.page_id = page_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def add_image(self, image_url: str) -> bool:
        """add just the image to notion page"""
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
    print("YouVersion -> Notion Sync (Ultra-Robust)")
    print("=" * 50)

    from dotenv import load_dotenv
    load_dotenv()

    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')

    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        print("Error: Missing configuration!")
        return 1

    # fetch verse with debugging
    fetcher = UltraRobustYouVersionFetcher(debug=True)
    verse_data = fetcher.get_verse_of_the_day()

    if not verse_data:
        print("Error: Could not fetch verse of the day")
        return 1

    print(f"\nVerse: {verse_data['citation']}")
    print(f"Image: {verse_data['image_url']}")

    # upload to notion (image only)
    uploader = NotionUploader(NOTION_TOKEN, NOTION_PAGE_ID)
    success = uploader.add_image(verse_data['image_url'])

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
