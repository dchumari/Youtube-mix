import random
import gdown
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Optional
from ..utils.logger import logger

class TwixtorProvider:
    def __init__(self, download_folder: str = "downloads/twixtors"):
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://animeworldtwixtor.com/popular-anime-twixtor/"

    def get_clips(self, num_series: int = 5, num_clips: int = 5) -> List[Path]:
        """
        Scrapes Twixtor links and downloads them.
        Returns a list of Paths to downloaded clips.
        """
        logger.info(f"Scraping Twixtors: {num_series} series, {num_clips} clips total.")
        
        try:
            # 1. Get Categories
            response = requests.get(self.base_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            categories = soup.find_all("figure", class_="wpb_wrapper vc_figure")

            all_category_links = []
            for category in categories:
                category_tag = category.select("a[href*='/category/']")
                if category_tag:
                    all_category_links.append(category_tag[0].get("href"))

            if not all_category_links:
                logger.error("No Twixtor categories found.")
                return []

            random.shuffle(all_category_links)
            
            # 2. Get Post Links from Categories
            post_links = []
            for category_url in all_category_links[:num_series]:
                try:
                    cat_resp = requests.get(category_url, timeout=10)
                    cat_soup = BeautifulSoup(cat_resp.content, "html.parser")
                    posts_container = cat_soup.find("div", class_="posts_container")
                    if not posts_container:
                        continue
                    
                    articles = posts_container.find_all("article", class_="post_item")
                    for article in articles:
                        link_tag = article.find("a", class_="simple")
                        if link_tag:
                            post_links.append(link_tag.get("href"))
                except Exception as e:
                    logger.warning(f"Failed to scrape category {category_url}: {e}")

            if not post_links:
                logger.error("No Twixtor posts found.")
                return []

            random.shuffle(post_links)
            
            # 3. Get Google Drive Links from Posts
            drive_links = []
            for post_url in post_links[:num_clips]:
                try:
                    post_resp = requests.get(post_url, timeout=10)
                    post_soup = BeautifulSoup(post_resp.content, "html.parser")
                    drive_btn = post_soup.select("a[class='wp-block-button__link wp-element-button']")
                    if drive_btn:
                        drive_links.append(drive_btn[0].get("href"))
                except Exception as e:
                    logger.warning(f"Failed to scrape post {post_url}: {e}")

            # 4. Download
            downloaded_paths = []
            for i, drive_url in enumerate(drive_links):
                target_path = self.download_folder / f"twixtor_{i + 1}.mp4"
                path = self._download_from_drive(drive_url, target_path)
                if path:
                    downloaded_paths.append(path)

            return downloaded_paths

        except Exception as e:
            logger.error(f"Twixtor scraping failed: {e}")
            return []

    def _download_from_drive(self, url: str, target_path: Path) -> Optional[Path]:
        """Handles Google Drive download via gdown."""
        try:
            # Normalize URL for gdown
            if "drive.google.com/file/d/" in url:
                file_id = url.split("/d/")[1].split("/")[0]
                url = f"https://drive.google.com/uc?id={file_id}"
            
            logger.info(f"Downloading from Drive: {url}")
            # gdown returns the path as a string
            result = gdown.download(url, str(target_path), quiet=True, fuzzy=True)
            if result:
                return Path(result)
        except Exception as e:
            logger.warning(f"Drive download failed: {url} -> {e}")
        return None
