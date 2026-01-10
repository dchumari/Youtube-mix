import asyncio
import glob
import os
import random
import re
import time
import unicodedata
from pathlib import Path

import requests
import zendriver as zd

from file_manager import clean_up
from upload_to_youtube import get_authenticated_service, upload_video

path = Path(__file__).parent
DOWNLOAD_LOCATION = path.parent / "downloads" / "youtube_shorts"
DOWNLOAD_LOCATION.mkdir(parents=True, exist_ok=True)


async def download_video(video_url, save_path):
    """
    Downloads a video from a given URL using the requests library in a streaming fashion.
    """
    try:
        # Send a GET request with stream=True to handle large files efficiently
        with requests.get(video_url, stream=True) as r:
            # Raise an exception if the request was unsuccessful (e.g., a 404 error)
            r.raise_for_status()

            # Open the local file in write-binary mode ('wb')
            with open(save_path, "wb") as f:
                print(f"Downloading to {save_path}...")
                # Iterate over the response content in chunks
                for chunk in r.iter_content(
                    chunk_size=8192
                ):  # Adjust chunk size as needed (e.g., 8 KB)
                    # Write each chunk to the file
                    if chunk:  # Filter out keep-alive new chunks
                        f.write(chunk)
            print("Download complete!")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except IOError as e:
        print(f"Error writing to file: {e}")


async def clean_text(raw_text):
    """
    Converts raw text (potentially with HTML, emojis, special chars) into a clean filename.
    """
    # 1. Remove HTML tags (like <h1>, </h1>)

    # 2. Remove or translate emojis and special symbols
    # Option A: Remove all non-ASCII characters (removes emojis)
    text = raw_text.encode("ascii", "ignore").decode("ascii")

    # Option B: Translate emojis to words (example: 🐐 -> "goat_emoji")
    # You would need a library like `emoji` for this. (See advanced version below)

    # 3. Remove or replace special characters (#, @, !, etc.)
    # Replace hashtags and other non-alphanumeric chars (except spaces) with underscores
    text = re.sub(
        r"[^\w\s-]", "", text
    )  # Keeps letters, numbers, underscores, spaces, hyphens
    text = re.sub(
        r"[-\s]+", "_", text
    )  # Replaces spaces and multiple hyphens with a single underscore

    # 4. Convert to lowercase and trim
    text = text.strip().lower()

    # 5. Ensure filename isn't empty and is reasonable length
    if not text:
        text = "untitled"
    if len(text) > 100:  # Limit length for practicality
        text = text[:100]

    return text


# async def search(query):
#     browser = await zd.start(headless=False)
#     query = query.replace(" ", "+")
#     url = f"https://urlebird.com/search/?q={query}"
#     page = await browser.get(url)

#     element = await page.select("#thumbs")
#     video_links = await element.query_selector_all(".info3 a[href*='/video/']")
#     # print(links)

#     for link in video_links:
#         href = link.get("href")
#         if not href:
#             continue

#         video_page = await page.get(href)
#         if not video_page:
#             continue

#         # Get video title (you'll need to adjust selector based on page structure)
#         try:
#             title_element = await video_page.select(".info2")
#         except Exception as e:
#             print(f"Error getting title element: {e}")
#             continue

#         video_title = (
#             await clean_text(title_element.text) if title_element else "No title found"
#         )

#         # Get video src URL
#         video_element = await video_page.select("video")
#         if not video_element:
#             continue

#         download_link = video_element.get("src")
#         print(f"\nTitle: {video_title}")
#         print(f"Video URL: {download_link}")

#         # Download video
#         if not download_link:
#             continue

#         filename = f"{video_title.strip().replace(' ', '_')}.mp4"
#         filepath = DOWNLOAD_LOCATION / filename

#         # await video_page.set_download_path(filepath)
#         await download_video(download_link, filepath)
#         print(f"Downloaded: {filepath}")

#         time.sleep(3)

#     await browser.stop()


async def post(title=None, description=None, downloaded_location=DOWNLOAD_LOCATION):
    # Implement your post logic here
    folder_path = Path(downloaded_location)

    if not folder_path.is_dir():
        print("\nFolder does not exist!")
        return False

    video_files = list(folder_path.glob("*.mp4"))
    if not video_files:
        print("\nNo .mp4 files found in the folder!")
        return False

    print(f"\nFound {len(video_files)} videos. Loading and shuffling...")

    video = random.choice(video_files)
    video_name = video.name

    youtube_service = get_authenticated_service(
        channel_name="phonkmixxx", client_secrets_file_name="client_secrets.json"
    )

    if title is None:
        title = video_name

    if description is None:
        description = (
            "Subscribe to phonkmixxx channel! to watch more phonk edits and mixes!"
        )

    upload_video(youtube_service, video, title, description)
    print(f"Posting: {video_name}")

    time.sleep(3)

    clean_up(folder_path)


# async def search(query, pages=5):
#     browser = await zd.start(headless=True)
#     query = query.replace(" ", "+")
#     url = f"https://urlebird.com/search/?q={query}"
#     page = await browser.get(url)

#     load_more = await page.select("#search_load_more")

#     for _ in range(pages):
#         if await load_more.get_position():
#             await load_more.click()
#             await asyncio.sleep(1)  # Wait for content to load
#         else:
#             print("Load more button not visible")
#             break

#     element = await page.select("#thumbs")
#     video_links = await element.query_selector_all(".info3 a[href*='/video/']")
#     print(f"found {len(video_links)} video links")

#     video = random.choice(video_links)

#     href = video.get("href")
#     if not href:
#         raise ValueError("No video link found")

#     video_page = await page.get(href)
#     if not video_page:
#         raise ValueError("Failed to load video page")

#     try:
#         title_element = await video_page.select(".info2")
#     except Exception as e:
#         print(f"Error getting title element: {e}")
#         title_element = None

#     video_title = (
#         await clean_text(title_element.text) if title_element else "No title found"
#     )

#     video_element = await video_page.select("video")
#     if not video_element:
#         raise ValueError("No video element found")

#     download_link = video_element.get("src")
#     print(f"\nTitle: {video_title}")
#     print(f"Video URL: {download_link}")

#     if not download_link:
#         raise ValueError("No download link found")

#     filename = f"{video_title.strip().replace(' ', '_')}.mp4"
#     filepath = DOWNLOAD_LOCATION / filename

#     # await video_page.set_download_path(filepath)
#     await download_video(download_link, filepath)
#     print(f"Downloaded: {filepath}")

#     time.sleep(3)

#     # for link in video_links:
#     #     href = link.get("href")
#     #     if not href:
#     #         continue

#     #     video_page = await page.get(href)
#     #     if not video_page:
#     #         continue

#     #     # Get video title (you'll need to adjust selector based on page structure)
#     #     try:
#     #         title_element = await video_page.select(".info2")
#     #     except Exception as e:
#     #         print(f"Error getting title element: {e}")
#     #         continue

#     #     video_title = (
#     #         await clean_text(title_element.text) if title_element else "No title found"
#     #     )

#     #     # Get video src URL
#     #     video_element = await video_page.select("video")
#     #     if not video_element:
#     #         continue

#     #     download_link = video_element.get("src")
#     #     print(f"\nTitle: {video_title}")
#     #     print(f"Video URL: {download_link}")

#     #     # Download video
#     #     if not download_link:
#     #         continue

#     #     filename = f"{video_title.strip().replace(' ', '_')}.mp4"
#     #     filepath = DOWNLOAD_LOCATION / filename

#     #     # await video_page.set_download_path(filepath)
#     #     await download_video(download_link, filepath)
#     #     print(f"Downloaded: {filepath}")

#     #     time.sleep(3)

#     await browser.stop()
#     return title_element.text if title_element else None


async def search(query, pages=5):
    browser = None
    try:
        browser = await zd.start(headless=True)
        query = query.replace(" ", "+")
        url = f"https://urlebird.com/search/?q={query}"
        page = await browser.get(url)

        # Load more pages
        for i in range(pages):
            try:
                # Re-find the load more button each time
                load_more = await page.select("#search_load_more")
                if not load_more:
                    print(f"No more content to load after {i + 1} pages")
                    break

                # Check if button is visible and clickable
                position = await load_more.get_position()
                if position:
                    await load_more.click()
                    # Increase wait time for content to fully load
                    await asyncio.sleep(2)
                    print(f"Loaded page {i + 1}/{pages}")
                else:
                    print("Load more button not visible")
                    break

            except Exception as e:
                print(f"Error loading page {i + 1}: {e}")
                # If we can't load more, continue with what we have
                break

        # Now get videos from the loaded content
        element = await page.select("#thumbs")
        if not element:
            raise ValueError("Could not find video container")

        video_links = await element.query_selector_all(".info3 a[href*='/video/']")
        print(f"Found {len(video_links)} video links")

        if not video_links:
            raise ValueError("No videos found")

        video = random.choice(video_links)
        href = video.get("href")

        if not href:
            raise ValueError("No video link found")

        # Open video in new tab to avoid stale references
        video_page = await browser.get(href)
        if not video_page:
            raise ValueError("Failed to load video page")

        # Get title
        try:
            title_element = await video_page.select(".info2")
            video_title = title_element.text if title_element else "No title found"
        except Exception as e:
            print(f"Error getting title: {e}")
            video_title = "No title found"

        description = video_title
        # Clean title
        video_title = await clean_text(video_title)

        # Get video element
        video_element = await video_page.select("video")
        if not video_element:
            raise ValueError("No video element found")

        download_link = video_element.get("src")
        if not download_link:
            raise ValueError("No download link found")

        print(f"\nTitle: {video_title}")
        print(f"Video URL: {download_link}")

        # Download video
        filename = f"{video_title.strip().replace(' ', '_')}.mp4"
        filepath = DOWNLOAD_LOCATION / filename

        await download_video(download_link, filepath)
        print(f"Downloaded: {filepath}")

        # Clean up browser
        if browser:
            await browser.stop()
            browser = None

        return description

    except Exception as e:
        print(f"Error in search: {e}")
        if browser:
            try:
                await browser.stop()
            except Exception as e:
                pass
        raise


async def main():
    description = await search("phonk edit", pages=30)
    # print("\nDescription: " + description)
    await post(title=description, description=description)


if __name__ == "__main__":
    asyncio.run(main())
