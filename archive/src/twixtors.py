import random
from pathlib import Path

import gdown
import requests
from bs4 import BeautifulSoup

path = Path(__file__).parent.resolve()
DOWNLOAD_DIR = path.parent / "downloads" / "twixtors"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def download_twixtors(url, filepath):
    # Convert Path object to string
    filepath_str = str(filepath)

    # Use the direct download URL format for Google Drive
    # Extract file ID from the view link
    if "drive.google.com/file/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
        url = f"https://drive.google.com/uc?id={file_id}"
    elif "drive.google.com/uc?id=" in url:
        url = str(url)
    else:
        return None

    # Download with fuzzy option to handle Google Drive links
    gdown.download(url, filepath_str, quiet=False, fuzzy=True)
    return filepath


def get_anime_clips(animes_series=5, anime_clips=5):
    if animes_series > 30 or anime_clips > 30:
        raise ValueError(
            "Number of anime_series or anime_clips must be at lesss than 30"
        )

    popular_twixtor = requests.get(
        "https://animeworldtwixtor.com/popular-anime-twixtor/"
    )

    soup = BeautifulSoup(popular_twixtor.content, "html.parser")
    categories = soup.find_all("figure", class_="wpb_wrapper vc_figure")

    all_categories = []
    for category in categories:
        category_tag = category.select("a[href*='/category/']")

        if not category_tag:
            continue

        category_link = category_tag[0].get("href")

        all_categories.append(category_link)

    random.shuffle(all_categories)

    print(f"Total categories: {len(all_categories)}")

    twixtors = []
    for category in all_categories[:animes_series]:
        twixtors_page = requests.get(category)
        twixtors_soup = BeautifulSoup(twixtors_page.content, "html.parser")
        twixtors_elements = twixtors_soup.find_all("article", class_="post_item")
        if not twixtors_elements:
            continue

        posts_container = twixtors_soup.find("div", class_="posts_container")

        if not posts_container:
            continue

        twixtors_article = posts_container.find_all("article", class_="post_item")
        if not twixtors_article:
            continue

        for twixtor_article in twixtors_article:
            twixtors_links = twixtor_article.find("a", class_="simple")
            if not twixtors_links:
                continue
            twixtors.append(twixtors_links.get("href"))

    random.shuffle(twixtors)

    drive_links = []
    for twixtor in twixtors[:anime_clips]:
        twixtor_page = requests.get(twixtor)
        twixtor_soup = BeautifulSoup(twixtor_page.content, "html.parser")
        drive_link = twixtor_soup.select(
            "a[class='wp-block-button__link wp-element-button']"
        )
        if drive_link:
            drive_links.append(drive_link[0].get("href"))

    for i, drive_link in enumerate(drive_links):
        done = download_twixtors(drive_link, DOWNLOAD_DIR / f"twixtor_{i + 1}.mp4")
        print(f"Downloaded {done}")

    # print(f"\nTotal drive: {len(drive_links)}")
    # print(f"drive_links: {drive_links}")

    # print(all_categories[:animes])


if __name__ == "__main__":
    get_anime_clips()
