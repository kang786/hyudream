import logging
import json
import re
from bs4 import BeautifulSoup
from src import utils

logger = logging.getLogger(__name__)

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def extract_html(html_path, output_path):
    logger.info(f"Extracting data from {html_path}...")
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        soup = BeautifulSoup(html_content, 'lxml')
        
        # The data seems to be inside a <pre> tag as a JSON string
        pre_tag = soup.find('pre')
        if not pre_tag:
            logger.error("No <pre> tag found in HTML. Cannot find JSON data.")
            return False
            
        json_content = pre_tag.get_text()
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON content: {e}")
            return False
            
        raw_list = data.get('city_total_list', [])
        if not raw_list:
            logger.warning("JSON parsed but 'city_total_list' is empty or missing.")
            
        extracted_records = []
        
        for item in raw_list:
            # Map JSON fields to our internal schema with evidence
            record = {
                "source_section": "json_api_dump",
                "evidence": {}
            }
            
            # Name
            name = clean_text(item.get('instltn_nm'))
            if name:
                record['name'] = name
                record['evidence']['name'] = item.get('instltn_nm')
                
            # Category
            cat = clean_text(item.get('instltn_purps'))
            if cat:
                record['category_raw'] = cat
                record['evidence']['category'] = item.get('instltn_purps')
                
            # Phone (General)
            phone = clean_text(item.get('gnrl_telno'))
            if phone:
                record['phone_raw'] = phone
                record['evidence']['phone'] = item.get('gnrl_telno')
            
            # Military Phone (Optional addition)
            gun_phone = clean_text(item.get('gun_telno'))
            if gun_phone:
                if 'phone_raw' in record:
                    record['phone_raw'] += f" / 군: {gun_phone}"
                else:
                    record['phone_raw'] = f"군: {gun_phone}"
                record['evidence']['phone_secondary'] = item.get('gun_telno')

            # Address
            addr = clean_text(item.get('dtl_addr'))
            city = clean_text(item.get('city'))
            if addr:
                record['address_raw'] = addr
                record['evidence']['address'] = item.get('dtl_addr')
            elif city:
                record['address_raw'] = city
                record['evidence']['address'] = item.get('city')
                
            # Notes / Introduction
            intro = clean_text(item.get('intrdt'))
            if intro:
                record['notes_raw'] = intro
                record['evidence']['notes'] = item.get('intrdt')
                
            # Hours (Check-in/out for lodging)
            enter = clean_text(item.get('entrnc_time'))
            leave = clean_text(item.get('lvrm_time'))
            if enter or leave:
                hours_str = f"입실: {enter}, 퇴실: {leave}" if enter and leave else (f"입실: {enter}" if enter else f"퇴실: {leave}")
                record['hours_raw'] = hours_str
                record['evidence']['hours'] = hours_str
                
            # Facilities / Convenience
            conv = clean_text(item.get('cnvnc_instltn'))
            if conv:
                if 'notes_raw' in record:
                    record['notes_raw'] += f" | 부대시설: {conv}"
                else:
                    record['notes_raw'] = f"부대시설: {conv}"
                record['evidence']['facilities'] = item.get('cnvnc_instltn')

            extracted_records.append(record)
            
        logger.info(f"Extracted {len(extracted_records)} raw records from JSON.")
        utils.save_json(output_path, extracted_records)
        return True
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False
