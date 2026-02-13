import requests
import logging
import os
from src import utils

def fetch_with_requests(url):
    """
    Fetches URL content using requests.
    Returns content if successful, None otherwise.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.warning(f"Requests fetch failed for {url}: {e}")
        return None

def fetch_with_playwright(url):
    """
    Fetches URL content using playwright.
    Returns content if successful, None otherwise.
    """
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, timeout=60000, wait_until="networkidle")
                content = page.content()
                return content
            except Exception as e:
                logging.error(f"Playwright navigation failed: {e}")
                return None
            finally:
                browser.close()
    except ImportError:
        logging.error("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        return None
    except Exception as e:
        logging.error(f"Playwright fetch failed: {e}")
        return None

def fetch_url(url, output_path, use_playwright="auto"):
    """
    Main fetch function.
    mode: 'auto' (try requests, fallback to playwright), 'always' (playwright only), 'never' (requests only)
    """
    logger = utils.setup_logging()
    logger.info(f"Fetching {url} (mode: {use_playwright})...")
    
    content = None
    
    if use_playwright == "never":
        content = fetch_with_requests(url)
    elif use_playwright == "always":
        content = fetch_with_playwright(url)
    else: # auto
        content = fetch_with_requests(url)
        if not content or len(content) < 500: # Heuristic: if content is too short, it might be a block or JS reload
            logger.info("Requests failed or returned suspicious content. Falling back to Playwright...")
            content = fetch_with_playwright(url)
            
    if content:
        utils.save_file(output_path, content)
        logger.info(f"Successfully saved content to {output_path} ({len(content)} bytes)")
        return True
    else:
        logger.error(f"Failed to fetch {url}")
        return False
