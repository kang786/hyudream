import logging
import json
import os
import sys
import re

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def setup_logging(log_file="data/logs.txt"):
    """
    Sets up logging to both console and file.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger()

def load_json(path):
    """
    Loads JSON from a file.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from {path}")
        return []
    except Exception as e:
        logging.error(f"Error loading JSON from {path}: {e}")
        return []

def save_json(path, data):
    """
    Saves data to a JSON file.
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved data to {path}")
    except Exception as e:
        logging.error(f"Error saving JSON to {path}: {e}")

def save_file(path, content, mode='w'):
    """
    Saves content to a file.
    """
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    try:
        with open(path, mode, encoding='utf-8' if 'b' not in mode else None) as f:
            f.write(content)
        logging.info(f"Saved content to {path}")
    except Exception as e:
        logging.error(f"Error saving file to {path}: {e}")
