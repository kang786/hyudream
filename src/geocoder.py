import logging
import time
import requests
import json
import os
import re
from src import utils

GEOCODE_CACHE_FILE = "data/geocode_cache.json"

def load_cache():
    return utils.load_json(GEOCODE_CACHE_FILE)

def save_cache(cache):
    utils.save_json(GEOCODE_CACHE_FILE, cache)

def geocode_nominatim(query):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {'User-Agent': 'ArmyWelfareMap/1.0'}
        params = {'q': query, 'format': 'json', 'limit': 1}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return {
                "lat": float(data[0]['lat']),
                "lng": float(data[0]['lon']),
                "provider": "nominatim",
                "ts": time.time(),
                "raw": data[0]
            }
        return None
    except Exception as e:
        logging.warning(f"Nominatim geocoding failed for '{query}': {e}")
        return None

def geocode_kakao(query, api_key):
    """카카오 지오코딩: 주소 검색 우선, 키워드 검색 폴백"""
    headers = {"Authorization": f"KakaoAK {api_key}"}
    
    # 1차: 주소 검색 API (정확도 높음)
    try:
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        params = {"query": query}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            return {
                "lat": float(doc['y']),
                "lng": float(doc['x']),
                "provider": "kakao_address",
                "ts": time.time(),
                "raw": doc
            }
    except Exception as e:
        logging.warning(f"Kakao address search failed for '{query}': {e}")
    
    # 2차: 키워드 검색 API (폴백)
    try:
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        params = {"query": query}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            return {
                "lat": float(doc['y']),
                "lng": float(doc['x']),
                "provider": "kakao_keyword",
                "ts": time.time(),
                "raw": doc
            }
    except Exception as e:
        logging.warning(f"Kakao keyword search failed for '{query}': {e}")
    
    return None


def geocode_data(input_path, output_path, provider="nominatim"):
    logger = logging.getLogger()
    logger.info(f"Geocoding data from {input_path} using {provider}...")
    
    data = utils.load_json(input_path)
    cache = load_cache()
    if not isinstance(cache, dict):
        cache = {}
        
    kakao_key = os.environ.get("KAKAO_REST_API_KEY")
    if provider == "kakao" and not kakao_key:
        logger.error("KAKAO_REST_API_KEY environment variable not set. Aborting.")
        return False
        
    updated_count = 0
    
    for record in data:
        # Skip if already has coordinates (optional: force re-geocode flag)
        if record.get("lat") and record.get("lng"):
            continue
            
        queries = []
        if record.get("address"):
            clean_addr = re.sub(r'\([^)]*\)', '', record["address"]).strip()
            queries.append(clean_addr)
            queries.append(record["address"]) # Backup original
            
        if record.get("address_raw"):
            clean_raw = re.sub(r'\([^)]*\)', '', record["address_raw"]).strip()
            queries.append(clean_raw)
            queries.append(utils.clean_text(record["address_raw"]))
            
        if record.get("name") and "city" in record: # heuristic placeholder
            queries.append(f"{record['city']} {record['name']}")
            
        # Deduplicate and filter empty
        queries = list(dict.fromkeys([q for q in queries if q]))
        
        result = None
        used_query = None
        
        for q in queries:
            if not q: continue
            
            # Check cache
            if q in cache:
                result = cache[q]
                logger.info(f"Cache hit for '{q}'")
                used_query = q
                break
            
            # API call
            logger.info(f"Geocoding '{q}'...")
            if provider == "kakao":
                result = geocode_kakao(q, kakao_key)
            else:
                result = geocode_nominatim(q)
                time.sleep(1.1) # Respect Nominatim rate limit
                
            if result:
                cache[q] = result
                save_cache(cache) # Save incrementally
                used_query = q
                break
                
        if result:
            record["lat"] = result["lat"]
            record["lng"] = result["lng"]
            record["confidence"] = min(1.0, record.get("confidence", 0.3) + 0.1)
            updated_count += 1
            
            # Save facilities.json incrementally (every 10 updates) to prevent data loss on stop
            if updated_count % 10 == 0:
                utils.save_json(output_path, data)
                logger.info(f"Intermediate save to {output_path} (Updated {updated_count} records so far)")
        else:
            if "notes" not in record: record["notes"] = ""
            record["notes"] += f" | 지오코딩 실패({provider})"
            
    utils.save_json(output_path, data)
    logger.info(f"Geocoding complete. Updated {updated_count} records.")
    return True
