import os
import json
import csv

# Configuration
COUNTRY_DATA_DIR = '/Users/jeetmukherjee/Desktop/PostPub/Development/postpub-backend-pipeline/country_data'
OUTPUT_FILE = '/Users/jeetmukherjee/Desktop/PostPub/Development/postpub-backend-pipeline/data/retraction_race_data.csv'
START_YEAR = 1996
END_YEAR = 2025

def main():
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Prepare CSV headers
    # Matches Flourish format: Country Name, Region, Image URL, 1996, 1997, ...
    years = [str(y) for y in range(START_YEAR, END_YEAR + 1)]
    headers = ['Country Name', 'Region', 'Image URL'] + years

    rows = []

    # Iterate over all files in the country_data directory
    files = sorted([f for f in os.listdir(COUNTRY_DATA_DIR) if f.endswith('_CountryPageData.json')])
    
    for filename in files:
        filepath = os.path.join(COUNTRY_DATA_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Extract basic info
            retraction_data = data.get('retraction_rate_data', {})
            country_name = retraction_data.get('country', '')
            
            # Skip if no country name
            if not country_name:
                # Fallback to extracting from filename if possible or skip
                # filename format: Afghanistan_CountryPageData.json
                country_name = filename.replace('_CountryPageData.json', '').replace('_', ' ')
            
            # Image URL (using the flag provided in JSON)
            raw_image_url = data.get('country_flag', '')
            # Remove leading slash if present to avoid double slashes when joining
            if raw_image_url.startswith('/'):
                raw_image_url = raw_image_url[1:]
            
            image_url = f"https://raw.githubusercontent.com/Ayush-pbh/rd-files-test/main/{raw_image_url}"
            
            # Region - not in JSON, leaving empty
            region = ''

            # Calculate cumulative retractions
            yearly_retractions = retraction_data.get('yearly_retractions', {})
            
            current_cumulative = 0
            row_data = {
                'Country Name': country_name,
                'Region': region,
                'Image URL': image_url
            }
            
            for year in range(START_YEAR, END_YEAR + 1):
                str_year = str(year)
                # Parse count, handling string/int differences just in case (though JSON usually has ints for values here)
                # The sample showed ints.
                count = yearly_retractions.get(str_year, 0)
                if isinstance(count, str):
                    count = int(count) if count.isdigit() else 0
                    
                current_cumulative += count
                row_data[str_year] = current_cumulative
            
            rows.append(row_data)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Write to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Successfully created CSV with {len(rows)} countries at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
