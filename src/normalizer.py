import logging
import hashlib
import re
from src import utils

logger = logging.getLogger(__name__)

def generate_id(name, phone, address):
    """
    Generates a stable ID based on name and (phone or address).
    """
    # Create a deterministic string
    base = f"{str(name).strip()}|{str(phone).strip()}|{str(address).strip()}"
    return hashlib.md5(base.encode('utf-8')).hexdigest()

def normalize_phone(phone_raw):
    """
    Standardizes phone numbers. 
    Removes non-dialable chars, keeps dashes if reasonable.
    """
    if not phone_raw:
        return None
    # If multiple numbers (e.g. "010-1234-5678 / 02-123-4567"), take the first one for the main field
    # But for now, let's just keep the text clean
    # Remove things that aren't digits, dashes, or separators
    cleaned = re.sub(r'[^\d\-\,\/]', '', str(phone_raw))
    return cleaned

def normalize_category(raw_cat, name):
    """
    Maps raw categories to standard ones based on category string and name.
    """
    text = (str(raw_cat) + " " + str(name)).lower()
    
    if any(x in text for x in ["숙박", "호텔", "콘도", "휴양", "회관", "resort", "hotel", "lodging"]):
        return "lodging"
    if any(x in text for x in ["체력", "골프", "체육", "헬스", "gym", "sports", "golf", "fitness"]):
        return "sports"
    if any(x in text for x in ["마트", "px", "내점", "쇼핑", "mart", "shop", "store"]):
        return "mart"
    if any(x in text for x in ["상담", "지원", "민원", "복지", "welfare"]):
        return "welfare_service"
    if any(x in text for x in ["문의", "전화", "콜센터", "contact"]):
        return "contact"
        
    return "other"

def calculate_confidence(record):
    score = 0.3
    if record.get("name"): score += 0.2
    if record.get("phone"): score += 0.2
    if record.get("address"): score += 0.2
    if record.get("homepage_or_booking_url"): score += 0.05
    # If we have hours or notes, slight boost
    if record.get("hours") or record.get("notes"): score += 0.05
    
    # Cap at 1.0
    return min(1.0, score)

def normalize_data(input_path, output_path):
    logger.info(f"Normalizing data from {input_path}...")
    
    try:
        raw_data = utils.load_json(input_path)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return False
        
    if not raw_data:
        logger.warning("No raw data to normalize.")
        return False

    normalized_records = []
    
    for item in raw_data:
        name = utils.clean_text(item.get("name", ""))
        phone_raw = item.get("phone_raw", "")
        address_raw = item.get("address_raw", "")
        
        # Skip if absolutely no info
        if not name and not phone_raw and not address_raw:
            continue
            
        category_raw = item.get("category_raw", "")
        
        record = {
            "id": generate_id(name, phone_raw, address_raw),
            "name": name,
            "category": normalize_category(category_raw, name),
            "category_raw": category_raw,
            "audience": item.get("audience_raw"), # Can be refined if specific patterns exist
            "audience_raw": item.get("audience_raw"),
            "phone": normalize_phone(phone_raw),
            "phone_raw": phone_raw,
            "address": address_raw, 
            "address_raw": address_raw,
            "lat": None,
            "lng": None,
            "homepage_or_booking_url": item.get("homepage_or_booking_url"),
            "hours": item.get("hours_raw"),
            "hours_raw": item.get("hours_raw"),
            "notes": item.get("notes_raw"),
            "notes_raw": item.get("notes_raw"),
            "source_section": item.get("source_section"),
            "confidence": 0.0, # detailed calc below
            "evidence": item.get("evidence", {})
        }
        
        record["confidence"] = calculate_confidence(record)
        normalized_records.append(record)
        
    # Deduplication logic (Name + Phone)
    unique_map = {}
    for rec in normalized_records:
        # Create a key for deduplication
        # If phone is missing, use address. If both missing, use just name (risky but acceptable for now)
        key_parts = [rec['name']]
        if rec['phone']:
            key_parts.append(rec['phone'])
        elif rec['address']:
            key_parts.append(rec['address'][:10]) # First 10 chars of address
        
        key = "_".join(key_parts)
        
        if key in unique_map:
            # Merge logic: favor the one with more info or just overwrite for now
            # In a real scenario, we'd check field by field.
            # Here, let's assume the new one might be better or same.
            # But let's keep the existing ID if possible to be stable? 
            # Actually ID is deterministic based on content, so it might change if content changes.
            pass 
        else:
            unique_map[key] = rec
            
    final_records = list(unique_map.values())
    
    logger.info(f"Normalized into {len(final_records)} records (from {len(raw_data)} raw).")
    utils.save_json(output_path, final_records)
    return True
