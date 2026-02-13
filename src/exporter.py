import json
import logging
from src import utils

def export_geojson(input_path, output_path):
    logger = logging.getLogger()
    logger.info(f"Exporting GeoJSON to {output_path}...")
    
    data = utils.load_json(input_path)
    features = []
    
    for record in data:
        if record.get("lat") is None or record.get("lng") is None:
            continue
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [record["lng"], record["lat"]]
            },
            "properties": {
                "id": record.get("id"),
                "name": record.get("name"),
                "category": record.get("category"),
                "phone": record.get("phone"),
                "address": record.get("address"),
                "homepage_or_booking_url": record.get("homepage_or_booking_url"),
                "hours": record.get("hours"),
                "audience": record.get("audience"),
                "notes": record.get("notes"),
                "confidence": record.get("confidence"),
                "source_section": record.get("source_section")
            }
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    utils.save_json(output_path, geojson)
    logger.info(f"Exported {len(features)} features to GeoJSON.")
    return True

def export_web_data(input_path, output_path):
    # For now, just copy the JSON, but maybe we want to filter fields
    logger = logging.getLogger()
    logger.info(f"Exporting Web JSON to {output_path}...")
    data = utils.load_json(input_path)
    # Ensure it's reachable by frontend (copy or symlink if needed, but here just save)
    utils.save_json(output_path, data)
    return True
