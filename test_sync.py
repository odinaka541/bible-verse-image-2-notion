"""
test script for debugging the youversion sync
allows you to test each component independently
"""

import os
from dotenv import load_dotenv
from youversion_sync_enhanced import EnhancedYouVersionFetcher, NotionUploader


def test_fetch_verse():
    """test fetching verse data"""
    print("=" * 50)
    print("Testing Verse Fetching")
    print("=" * 50)

    fetcher = EnhancedYouVersionFetcher()
    verse_data = fetcher.get_verse_of_the_day()

    if verse_data:
        print("\nSuccessfully fetched verse!")
        print(f"Citation: {verse_data['citation']}")
        print(f"Passage: {verse_data['passage']}")
        print(f"Image URL: {verse_data['image_url']}")
        print(f"Date: {verse_data['date']}")
        return verse_data
    else:
        print("\nFailed to fetch verse")
        return None


def test_notion_connection(verse_data):
    """test notion api connection"""
    print("\n" + "=" * 50)
    print("Testing Notion Connection")
    print("=" * 50)

    load_dotenv()

    NOTION_TOKEN = os.getenv('NOTION_TOKEN')
    NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')

    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        print("Error: Missing Notion credentials in .env")
        return False

    print(f"Token: {NOTION_TOKEN[:20]}...")
    print(f"Page ID: {NOTION_PAGE_ID}")

    uploader = NotionUploader(NOTION_TOKEN, NOTION_PAGE_ID)

    # try a simple test block first
    try:
        import requests
        url = f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children"
        headers = uploader.headers

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        print("\nNotion API connection successful!")
        print(f"Page has {len(response.json().get('results', []))} existing blocks")

        # now try uploading the verse
        if verse_data:
            print("\nUploading verse to Notion...")
            success = uploader.add_verse_with_image(
                verse_data['citation'],
                verse_data['passage'],
                verse_data['image_url']
            )
            return success

    except requests.exceptions.HTTPError as e:
        print(f"\nNotion API Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\nConnection failed: {e}")
        return False


def main():
    print("\nYouVersion -> Notion Sync Test Suite\n")

    # test 1: fetch verse
    verse_data = test_fetch_verse()

    if not verse_data:
        print("\nCannot proceed with Notion test without verse data")
        return

    # test 2: upload to notion
    user_input = input("\nProceed with Notion upload test? (y/n): ")
    if user_input.lower() == 'y':
        test_notion_connection(verse_data)
    else:
        print("\nSkipping Notion test")

    print("\nTest suite complete!")


if __name__ == "__main__":
    main()
