import pandas as pd
import json
import os
import re
from collections import defaultdict
from datetime import datetime

def classify_retractions_df(df, classification_patterns):
    """
    Classify retractions in the DataFrame using the same logic as retraction_classification.py.
    Uses str.contains(pattern, case=False) on the Reason column for each category.
    Returns a DataFrame with classification columns.
    """
    # Initialize classification columns
    df['research'] = False
    df['integrity'] = False
    df['supplemental'] = False
    df['system'] = False
    df['alterations'] = False
    
    # Apply classification for each category (same as retraction_classification.py)
    for category, pattern in classification_patterns.items():
        if pattern:
            # Use str.contains with case=False (same as retraction_classification.py)
            mask = df['Reason'].str.contains(pattern, case=False, na=False)
            df.loc[mask, category] = True
    
    return df

def load_classification_files():
    """
    Load classification keywords from text files in the classification folder.
    Uses the same approach as retraction_classification.py.
    Returns a dict with category -> regex pattern for str.contains matching.
    """
    classification_patterns = {
        'research': None,
        'integrity': None,
        'supplemental': None,
        'system': None,
        'alterations': None
    }
    
    # Classification folder path (relative to script location or project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    classification_folder = os.path.join(project_root, 'classification')
    
    # Map file names to categories (matching retraction_classification.py logic)
    # Note: retraction_classification.py uses: Supplemental, System, Research, Integrity, Serious
    file_mapping = {
        'Research.txt': 'research',
        'Integrity.txt': 'integrity',
        'Supplemental.txt': 'supplemental',
        'System.txt': 'system',
        'Serious.txt': 'alterations'  # Serious.txt maps to alterations
    }
    
    for filename, category in file_mapping.items():
        filepath = os.path.join(classification_folder, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f if line.strip()]
                    if keywords:
                        # Create regex pattern for str.contains (same as retraction_classification.py)
                        pattern = '|'.join(keywords)
                        classification_patterns[category] = pattern
                        print(f"Loaded {len(keywords)} keywords from {filename} for {category}")
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
        else:
            print(f"Warning: Classification file not found: {filepath}")
    
    return classification_patterns


def get_country_flag_path(country_name):
    """
    Generate country flag path from country name.
    """
    # Replace special characters and spaces
    flag_name = country_name.replace(' ', '_').replace('(', '').replace(')', '')
    # Handle special cases
    flag_name = flag_name.replace('formerly_Burma', 'formerly_Burma')
    flag_name = flag_name.replace('&', '_')
    return f"/country_flags/{flag_name}.svg"

def parse_original_paper_date(date_str):
    """
    Parse OriginalPaperDate and extract the year.
    Handles formats like '12/16/2025 0:00' or '2025-12-16'
    """
    if pd.isna(date_str) or str(date_str).strip() == '':
        return None
    
    date_str = str(date_str).strip()
    
    # Try different date formats
    date_formats = [
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%Y/%m/%d'
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str.split()[0], fmt.split()[0])  # Take first part before space
            return dt.year
        except (ValueError, IndexError):
            continue
    
    # If all formats fail, try to extract year from string
    try:
        # Look for 4-digit year
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            return int(year_match.group())
    except:
        pass
    
    return None

def load_publication_data_from_scimago(scimago_file=None):
    """
    Load publication data from scimago_combined.csv.
    Looks in data/ folder first, then current directory.
    """
    if scimago_file is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        scimago_file = os.path.join(project_root, 'data', 'scimago_combined.csv')
        # Fallback to current directory
        if not os.path.exists(scimago_file):
            scimago_file = 'scimago_combined.csv'
    """
    Load publication data from scimago_combined.csv and sum all years from 1996-2024.
    Returns a dict with country -> total_publications (sum of all years).
    """
    if not os.path.exists(scimago_file):
        print(f"Warning: {scimago_file} not found")
        return {}
    
    publication_data = {}
    try:
        df = pd.read_csv(scimago_file)
        
        # Get year columns (1996-2024)
        year_columns = [str(year) for year in range(1996, 2025)]
        
        # Sum all years for each country
        for _, row in df.iterrows():
            country = str(row['Country']).strip()
            if country:
                total_publications = 0
                for year_col in year_columns:
                    if year_col in df.columns:
                        value = row[year_col]
                        if pd.notna(value):
                            try:
                                total_publications += float(value)
                            except (ValueError, TypeError):
                                pass
                
                if total_publications > 0:
                    publication_data[country] = total_publications
        
        print(f"Loaded publication data for {len(publication_data)} countries from {scimago_file}")
        print(f"Total publications range: {min(publication_data.values()):.0f} - {max(publication_data.values()):.0f}")
        
    except Exception as e:
        print(f"Warning: Could not load publication data from {scimago_file}: {e}")
    
    return publication_data

def load_publication_data(publication_file=None):
    """
    Load publication data. If no file specified, tries to load from scimago_combined.csv.
    Expected format: country -> total_publications
    """
    # Default to scimago_combined.csv if no file specified
    if publication_file is None:
        return load_publication_data_from_scimago()
    
    if not os.path.exists(publication_file):
        # Fallback to scimago_combined.csv
        print(f"Publication file {publication_file} not found, trying scimago_combined.csv")
        return load_publication_data_from_scimago()
    
    publication_data = {}
    try:
        if publication_file.endswith('.csv'):
            # Check if it's the scimago format
            if 'scimago' in publication_file.lower():
                return load_publication_data_from_scimago(publication_file)
            
            # Otherwise, assume simple CSV format
            df = pd.read_csv(publication_file)
            if len(df.columns) >= 2:
                for _, row in df.iterrows():
                    country = str(row.iloc[0]).strip()
                    publications = row.iloc[1]
                    if pd.notna(publications):
                        publication_data[country] = float(publications)
        elif publication_file.endswith('.json'):
            with open(publication_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    publication_data = data
                elif isinstance(data, list):
                    for item in data:
                        if 'country' in item and 'publications' in item:
                            publication_data[item['country']] = float(item['publications'])
    except Exception as e:
        print(f"Warning: Could not load publication data: {e}")
    
    return publication_data

def calculate_retraction_rate(total_retractions, total_publications=None):
    """
    Calculate retraction rate per 1000 publications.
    Formula: (total_retractions / total_publications) * 1000
    """
    if total_publications is None or total_publications == 0:
        return 0.0
    else:
        return round((total_retractions / total_publications) * 1000, 4)

def process_csv_to_json(csv_file_path, output_json_path, publication_file=None):
    """
    Process the CSV file and generate the dashboard JSON.
    
    Args:
        csv_file_path: Path to the input CSV file
        output_json_path: Path to the output JSON file
        publication_file: Optional path to a file containing publication counts per country
    """
    print(f"Reading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    print(f"Loaded {len(df)} records")
    
    # Parse OriginalPaperDate and filter to >= 1996
    print("Parsing OriginalPaperDate and filtering to >= 1996...")
    df['original_paper_year'] = df['OriginalPaperDate'].apply(parse_original_paper_date)
    
    # Filter to only include records from 1996 onwards
    initial_count = len(df)
    df = df[df['original_paper_year'] >= 1996]
    filtered_count = len(df)
    print(f"Filtered to {filtered_count} records (from {initial_count}) based on OriginalPaperDate >= 1996")
    
    # Count records with valid dates
    valid_dates = df['original_paper_year'].notna().sum()
    print(f"Records with valid OriginalPaperDate >= 1996: {valid_dates}/{len(df)}")
    
    if valid_dates > 0:
        year_counts = df['original_paper_year'].value_counts().sort_index()
        print(f"Original paper year range: {year_counts.index.min()} - {year_counts.index.max()}")
    
    # Load publication data from scimago_combined.csv (default)
    publication_data = load_publication_data(publication_file)
    if publication_data:
        print(f"Loaded publication data for {len(publication_data)} countries")
    else:
        print("Warning: No publication data available. Retraction rates will be set to 0.0")
    
    # Load classification files from classification folder (using retraction_classification.py approach)
    classification_patterns = load_classification_files()
    use_file_classification = any(classification_patterns.values())
    
    if use_file_classification:
        print("Using classification files from classification/ folder for categorization")
        print("Using str.contains pattern matching (same as retraction_classification.py)")
    else:
        print("Warning: No classification files found. Cannot classify retractions.")
        return []
    
    # Classify all retractions using the same method as retraction_classification.py
    print("Classifying retractions...")
    df = classify_retractions_df(df, classification_patterns)
    
    # Initialize country statistics
    country_stats = defaultdict(lambda: {
        'alterations': 0,
        'research': 0,
        'integrity': 0,
        'supplemental': 0,
        'system': 0,
        'total': 0
    })
    
    # Process each row
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(f"Processing row {idx}/{len(df)}")
        
        # Get countries (can be multiple, separated by semicolons)
        countries_str = str(row.get('Country', ''))
        if pd.isna(countries_str) or countries_str.lower() in ['unknown', 'nan', '']:
            continue
        
        # Split countries
        countries = [c.strip() for c in countries_str.split(';') if c.strip()]
        
        # Get classifications from the DataFrame columns (already set by classify_retractions_df)
        classifications = {
            'alterations': row.get('alterations', False),
            'research': row.get('research', False),
            'integrity': row.get('integrity', False),
            'supplemental': row.get('supplemental', False),
            'system': row.get('system', False)
        }
        
        # Update statistics for each country
        for country in countries:
            if country:
                country_stats[country]['total'] += 1
                if classifications['alterations']:
                    country_stats[country]['alterations'] += 1
                if classifications['research']:
                    country_stats[country]['research'] += 1
                if classifications['integrity']:
                    country_stats[country]['integrity'] += 1
                if classifications['supplemental']:
                    country_stats[country]['supplemental'] += 1
                if classifications['system']:
                    country_stats[country]['system'] += 1
    
    print(f"Processed {len(country_stats)} countries")
    
    # Convert to list format and calculate retraction_rate
    result = []
    for country, stats in country_stats.items():
        # Calculate total retractions as sum of all categories
        # Total = Supplemental + System + Research + Integrity + Serious (alterations)
        total_retractions = (stats['supplemental'] + stats['system'] + 
                            stats['research'] + stats['integrity'] + 
                            stats['alterations'])
        
        # Get total publications for this country
        total_publications = publication_data.get(country)
        
        # Calculate retraction_rate: (total_retractions / total_publications) * 1000
        retraction_rate = calculate_retraction_rate(total_retractions, total_publications)
        
        result.append({
            'country': country,
            'alterations': stats['alterations'],
            'research': stats['research'],
            'integrity': stats['integrity'],
            'supplemental': stats['supplemental'],
            'system': stats['system'],
            'total': total_retractions,  # Use sum of all categories, not unique record count
            'retraction_rate': retraction_rate,
            'country_flag': get_country_flag_path(country)
        })
    
    # Sort by total (descending)
    result.sort(key=lambda x: x['total'], reverse=True)
    
    # Write to JSON file
    print(f"Writing JSON to: {output_json_path}")
    with open(output_json_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Successfully generated JSON file with {len(result)} countries")
    return result

if __name__ == '__main__':
    import sys
    
    # Default file paths (look in data/ folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_csv = os.path.join(project_root, 'data', 'retraction_watch.csv')
    if not os.path.exists(default_csv):
        default_csv = 'retraction_watch.csv'
    
    csv_file = default_csv
    json_file = 'dashboard_table.json'
    publication_file = None
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    if len(sys.argv) > 2:
        json_file = sys.argv[2]
    if len(sys.argv) > 3:
        publication_file = sys.argv[3]
    
    process_csv_to_json(csv_file, json_file, publication_file)

