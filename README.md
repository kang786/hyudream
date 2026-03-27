# Army Welfare Map Visualization (휴드림 지도) https://kang786.github.io/hyudream-/

This tool visualizes Army Welfare facilities (hotels, marts, etc.) on an interactive map. It is designed to work offline by processing pre-fetched data.

## Features
- **Offline Extraction**: Parses raw HTML/JSON dumps from welfare.army.mil.kr.
- **Normalization**: Standardizes category names (Lodging, Mart, Sports, etc.) and formats phone numbers.
- **Geocoding**: Supports Nominatim (OSM) and Kakao Maps API for finding coordinates.
- **Web Map**: simple Leaflet-based frontend to visualize the data.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables** (Optional):
   - `KAKAO_REST_API_KEY`: Required if usage of Kakao Geocoder is intended.

## Usage

### 1. Fetch Data (Optional)
If you have internet access, you can fetch the latest data.
```bash
python main.py fetch --url "https://welfare.army.mil.kr/mTel.do"
```
*Note: If `data/raw/source.html` already exists, you can skip this.*

### 2. Extract & Normalize
Parses the raw HTML/JSON and creates a clean `facilities.json`.
```bash
python main.py extract
```
Output: `data/facilities.json`

### 3. Geocode
Finds lat/lng coordinates for addresses.
```bash
python main.py geocode --provider nominatim
```
*Use `--provider kakao` for better accuracy in Korea (requires API key).*

### 4. Export
Generates GeoJSON for GIS and JSON for the web app.
```bash
python main.py export
```
Output: `data/facilities.geojson`, `web/data.json`

### 5. Serve Web Map
Starts a local web server to view the map.
```bash
python main.py serve
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

## Pipeline
Run all steps in order:
```bash
python main.py pipeline
```

## Directory Structure
- `src/`: Python source code (extractor, geocoder, etc.)
- `web/`: Frontend code (HTML, JS, CSS)
- `data/`: Processed data
- `data/raw/`: Raw input files
