import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Army Welfare mTel Map Visualization Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch data from URL")
    fetch_parser.add_argument("--url", default="https://welfare.army.mil.kr/mTel.do", help="Target URL")
    fetch_parser.add_argument("--out", default="data/raw/source.html", help="Output path for HTML")
    fetch_parser.add_argument("--use-playwright", choices=["auto", "always", "never"], default="auto", help="Use Playwright for fetching")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract data from HTML")
    extract_parser.add_argument("--input", default="data/raw/source.html", help="Input HTML file")
    extract_parser.add_argument("--out", default="data/facilities.json", help="Output JSON file")

    # Geocode command
    geocode_parser = subparsers.add_parser("geocode", help="Geocode extracted data")
    geocode_parser.add_argument("--input", default="data/facilities.json", help="Input JSON file")
    geocode_parser.add_argument("--out", default="data/facilities.json", help="Output JSON file (updated)")
    geocode_parser.add_argument("--provider", choices=["nominatim", "kakao"], default="nominatim", help="Geocoding provider")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export data for web/GIS")
    export_parser.add_argument("--input", default="data/facilities.json", help="Input JSON file")
    export_parser.add_argument("--geojson", default="data/facilities.geojson", help="Output GeoJSON file")
    export_parser.add_argument("--web", default="web/data.json", help="Output Web JSON file")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Serve web app locally")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to serve on")

    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run end-to-end pipeline")
    pipeline_parser.add_argument("--url", default="https://welfare.army.mil.kr/mTel.do", help="Target URL")
    pipeline_parser.add_argument("--provider", choices=["nominatim", "kakao"], default="nominatim", help="Geocoding provider")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "fetch":
        from src import fetcher
        fetcher.fetch_url(args.url, args.out, args.use_playwright)
    
    elif args.command == "extract":
        from src import extractor
        from src import normalizer
        import logging
        
        # Step 1: Extract raw
        raw_data = extractor.extract_html(args.input, args.out) # Modified to return list
        if raw_data:
             # Temp save raw? or just pass to normalizer
             # To stick to file-based interface for modularity:
             pass 
             
        # Actually `extractor.extract_html` in my implementation saves to file.
        # So we just run normalizer on that file?
        # The spec says: extract runs extract. 
        # But normalizer is needed to make "facilities.json" fit the schema.
        # So let's run extract -> raw.json, then normalizer -> facilities.json?
        # Or just extract+normalize in one go.
        # Let's check `extractor.py`: it saves to `output_path`.
        # `normalizer.py`: reads input, saves output.
        
        # We need a temporary path for raw extraction if we want to run both.
        # Or we overwrite. 
        temp_raw = args.out + ".raw.json"
        
        if extractor.extract_html(args.input, temp_raw):
             normalizer.normalize_data(temp_raw, args.out)
             # os.remove(temp_raw) # Optional cleanup
             print(f"Extraction and normalization complete. Saved to {args.out}")

    elif args.command == "geocode":
        from src import geocoder
        geocoder.geocode_data(args.input, args.out, args.provider)

    elif args.command == "export":
        from src import exporter
        exporter.export_geojson(args.input, args.geojson)
        exporter.export_web_data(args.input, args.web)


    elif args.command == "serve":
        print(f"Serving on port {args.port}...")
        import http.server
        import socketserver
        
        # Change directory to web/ for serving
        os.chdir("web")
        Handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", args.port), Handler) as httpd:
            print(f"Serving at http://localhost:{args.port}")
            httpd.serve_forever()

    elif args.command == "pipeline":
        print("Running pipeline...")
        from src import fetcher
        from src import extractor
        from src import normalizer
        from src import geocoder
        from src import exporter
        # import os  <-- Removed redundant import that shadowed global scope

        
        # 0. Setup paths
        raw_html = "data/raw/source.html"
        raw_json = "data/raw/extracted.json"
        facilities_json = "data/facilities.json"
        geojson_out = "data/facilities.geojson"
        web_json_out = "web/data.json"
        
        # 1. Fetch
        print(f"[1/5] Fetching {args.url}...")
        if not fetcher.fetch_url(args.url, raw_html):
            print("Fetch failed. Checking if offline file exists...")
            if not os.path.exists(raw_html):
                print("No offline file found. Aborting.")
                sys.exit(1)
        
        # 2. Extract
        print("[2/5] Extracting...")
        if not extractor.extract_html(raw_html, raw_json):
            print("Extraction failed.")
            sys.exit(1)
            
        # 3. Normalize
        print("[3/5] Normalizing...")
        if not normalizer.normalize_data(raw_json, facilities_json):
            print("Normalization failed.")
            sys.exit(1)
            
        # 4. Geocode
        print(f"[4/5] Geocoding (Provider: {args.provider})...")
        geocoder.geocode_data(facilities_json, facilities_json, args.provider)
        
        # 5. Export
        print("[5/5] Exporting...")
        exporter.export_geojson(facilities_json, geojson_out)
        exporter.export_web_data(facilities_json, web_json_out)
        
        print("Pipeline complete!")
        print(f"Run 'python main.py serve' to view the map.")



if __name__ == "__main__":
    main()
