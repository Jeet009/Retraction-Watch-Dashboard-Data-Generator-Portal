import pandas as pd
import json
import os
from collections import defaultdict
from datetime import datetime

def parse_retraction_date(date_str):
    """
    Parse RetractionDate and extract the year.
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

def classify_retraction(row):
    """
    Classify a retraction into categories based on ArticleType and Reason fields.
    Note: A retraction can belong to multiple categories.
    """
    classifications = {
        'research': False,
        'integrity': False,
        'supplemental': False,
        'system': False,
        'alterations': False
    }
    
    # Check ArticleType for research category
    article_type = str(row.get('ArticleType', '')).lower()
    if 'research article' in article_type or 'review article' in article_type:
        classifications['research'] = True
    
    # Check Reason field for other categories
    reason = str(row.get('Reason', '')).lower()
    
    # Integrity-related keywords (more specific)
    integrity_keywords = [
        'plagiarism', 'fabrication', 'falsification',
        'unreliable results and/or conclusions',
        'concerns/issues about data', 'concerns/issues about image',
        'paper mills', 'euphemisms for plagiarism',
        'plagiarism of data', 'plagiarism of image'
    ]
    if any(keyword in reason for keyword in integrity_keywords):
        classifications['integrity'] = True
    
    # Supplemental-related keywords
    supplemental_keywords = [
        'supplemental', 'supplementary', 'correction', 'erratum'
    ]
    if any(keyword in reason for keyword in supplemental_keywords):
        classifications['supplemental'] = True
    
    # System-related keywords (peer review, editorial issues)
    system_keywords = [
        'compromised peer review', 'concerns/issues about peer review',
        'investigation by journal/publisher', 'investigation by journal',
        'investigation by publisher'
    ]
    if any(keyword in reason for keyword in system_keywords):
        classifications['system'] = True
    
    # Alterations-related keywords (duplication, authorship issues, etc.)
    alterations_keywords = [
        'duplication', 'duplication of/in article', 'duplication of data',
        'duplication of/in image', 'euphemisms for duplication',
        'concerns/issues about authorship/affiliation',
        'concerns/issues about referencing/attributions',
        'concerns/issues about third party involvement'
    ]
    if any(keyword in reason for keyword in alterations_keywords):
        classifications['alterations'] = True
    
    return classifications

def load_classification_files():
    """
    Load classification keywords from text files in the classification folder.
    Returns a dict with category -> list of keywords.
    """
    classification = {
        'research': [],
        'integrity': [],
        'supplemental': [],
        'system': [],
        'alterations': []
    }
    
    # Classification folder path (relative to script location or project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    classification_folder = os.path.join(project_root, 'classification')
    
    # Map file names to categories
    # Note: Serious.txt contains duplication items which map to alterations
    file_mapping = {
        'Research.txt': 'research',
        'Integrity.txt': 'integrity',
        'Supplemental.txt': 'supplemental',
        'System.txt': 'system',
        'Serious.txt': 'alterations'  # Serious.txt contains duplication items
    }
    
    for filename, category in file_mapping.items():
        filepath = os.path.join(classification_folder, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    keywords = [line.strip() for line in f if line.strip()]
                    classification[category] = [kw.lower() for kw in keywords]
                    print(f"Loaded {len(keywords)} keywords from {filename} for {category}")
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
        else:
            print(f"Warning: Classification file not found: {filepath}")
    
    return classification

def classify_with_files(row, classification_keywords):
    """
    Classify retraction using keywords from files.
    """
    classifications = {
        'research': False,
        'integrity': False,
        'supplemental': False,
        'system': False,
        'alterations': False
    }
    
    # Check ArticleType for research
    article_type = str(row.get('ArticleType', '')).lower()
    if 'research article' in article_type or 'review article' in article_type:
        classifications['research'] = True
    
    # Check Reason field with classification keywords
    reason = str(row.get('Reason', ''))
    reason_lower = reason.lower()
    
    # Check each category
    for category, keywords in classification_keywords.items():
        if category == 'research':
            # Research is already handled by ArticleType above
            continue
        
        if keywords:
            # Check if any keyword from the category appears in the reason
            for keyword in keywords:
                if keyword in reason_lower:
                    classifications[category] = True
                    break  # Found a match for this category, move to next
    
    return classifications

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

def normalize_country_name(name):
    """
    Normalize country name by removing parentheses, 'formerly' notes, and common variations.
    """
    import re
    # Remove content in parentheses (e.g., "Brunei (Brunei Darussalam)" -> "Brunei")
    name = re.sub(r'\s*\([^)]*\)', '', name)
    # Remove "formerly" notes (e.g., "Myanmar (formerly Burma)" -> "Myanmar")
    name = re.sub(r'\s*\(formerly[^)]*\)', '', name, flags=re.IGNORECASE)
    # Remove common prefixes/suffixes
    name = name.replace('Island', '').replace('Islands', '').strip()
    # Normalize common abbreviations
    name = name.replace('&', 'and').replace('St.', 'Saint').replace('St ', 'Saint ')
    # Remove extra whitespace
    name = ' '.join(name.split())
    return name.strip()

def find_similar_country(country_name, scimago_countries, threshold=0.7):
    """
    Find a similar country name in scimago_countries using fuzzy matching.
    Returns the best match if similarity is above threshold, else None.
    """
    from difflib import SequenceMatcher
    
    # Manual mappings for common cases
    manual_mappings = {
        'russia': 'Russian Federation',
        'brunei': 'Brunei Darussalam',
        'myanmar': 'Myanmar',
        'burma': 'Myanmar',
        'syria': 'Syrian Arab Republic',
        'north macedonia': 'Macedonia',
        'macedonia': 'Macedonia',
        'eswatini': 'Eswatini',
        'swaziland': 'Eswatini',
        'republic of the congo': 'Congo',
        'congo-brazzaville': 'Congo',
        'réunion island': 'Reunion',
        'reunion island': 'Reunion',
        'reunion': 'Reunion',
        'st. kitts & nevis': 'Saint Kitts and Nevis',
        'st kitts & nevis': 'Saint Kitts and Nevis',
        'saint kitts & nevis': 'Saint Kitts and Nevis',
        'east timor': 'Timor-Leste',
        'timor-leste': 'Timor-Leste',
        'sint maarten': 'Netherlands Antilles',  # May not exist, but try
    }
    
    # Normalize the input country name
    normalized_input = normalize_country_name(country_name).lower()
    
    # Check manual mappings first
    if normalized_input in manual_mappings:
        mapped = manual_mappings[normalized_input]
        if mapped in scimago_countries:
            return mapped
    
    # Also check if normalized input matches any part of manual mapping keys
    for key, mapped in manual_mappings.items():
        if key in normalized_input or normalized_input in key:
            if mapped in scimago_countries:
                return mapped
    
    country_name_lower = country_name.lower().strip()
    normalized_input = normalized_input if normalized_input else country_name_lower
    best_match = None
    best_ratio = 0
    
    for scimago_country in scimago_countries:
        scimago_lower = scimago_country.lower().strip()
        scimago_normalized = normalize_country_name(scimago_country).lower()
        
        # Check if normalized names match exactly
        if normalized_input == scimago_normalized:
            return scimago_country
        
        # Check if one contains the other (e.g., "Russia" in "Russian Federation")
        if normalized_input in scimago_lower or scimago_lower in normalized_input:
            ratio = SequenceMatcher(None, normalized_input, scimago_lower).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = scimago_country
        
        # Check normalized versions
        if normalized_input in scimago_normalized or scimago_normalized in normalized_input:
            ratio = SequenceMatcher(None, normalized_input, scimago_normalized).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = scimago_country
        
        # Also check similarity ratio on normalized names
        ratio = SequenceMatcher(None, normalized_input, scimago_normalized).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = scimago_country
        
        # Check original names too
        ratio = SequenceMatcher(None, country_name_lower, scimago_lower).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = scimago_country
    
    if best_ratio >= threshold:
        return best_match
    return None

def load_publication_data_from_scimago(scimago_file=None):
    """
    Load publication data from scimago_combined.csv and sum all years from 1996-2024.
    Returns: (publication_data dict, scimago_countries list)
    """
    if scimago_file is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        scimago_file = os.path.join(project_root, 'data', 'scimago_combined.csv')
        # Fallback to current directory
        if not os.path.exists(scimago_file):
            scimago_file = 'scimago_combined.csv'
    
    if not os.path.exists(scimago_file):
        print(f"Warning: {scimago_file} not found")
        return {}, []
    
    publication_data = {}
    scimago_countries = []
    
    try:
        df = pd.read_csv(scimago_file)
        
        # Get year columns (1996-2024)
        year_columns = [str(year) for year in range(1996, 2025)]
        
        # Sum all years for each country
        for _, row in df.iterrows():
            country = str(row['Country']).strip()
            if country:
                scimago_countries.append(country)
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
        if publication_data:
            print(f"Total publications range: {min(publication_data.values()):.0f} - {max(publication_data.values()):.0f}")
        
    except Exception as e:
        print(f"Warning: Could not load publication data from {scimago_file}: {e}")
    
    return publication_data, scimago_countries

def load_publication_data(publication_file=None):
    """
    Load publication data. If no file specified, tries to load from scimago_combined.csv.
    Expected format: country -> total_publications
    Returns: (publication_data, scimago_countries)
    """
    # Default to scimago_combined.csv if no file specified
    if publication_file is None:
        return load_publication_data_from_scimago()
    
    if not os.path.exists(publication_file):
        # Fallback to scimago_combined.csv
        print(f"Publication file {publication_file} not found, trying scimago_combined.csv")
        return load_publication_data_from_scimago()
    
    publication_data = {}
    scimago_countries = []
    
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
                        scimago_countries.append(country)
        elif publication_file.endswith('.json'):
            with open(publication_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    publication_data = data
                    scimago_countries = list(data.keys())
                elif isinstance(data, list):
                    for item in data:
                        if 'country' in item and 'publications' in item:
                            country = item['country']
                            publication_data[country] = float(item['publications'])
                            scimago_countries.append(country)
    except Exception as e:
        print(f"Warning: Could not load publication data: {e}")
    
    return publication_data, scimago_countries

def calculate_retraction_rate(total_retractions, total_publications=None):
    """
    Calculate retraction rate per 1000 publications.
    Formula: (total_retractions / total_publications) * 1000
    """
    if total_publications is None or total_publications == 0:
        return 0.0
    else:
        return round((total_retractions / total_publications) * 1000, 4)

def process_csv_to_json_by_retraction_date(csv_file_path, output_json_path, publication_file=None, min_year=None, max_year=None):
    """
    Process the CSV file and generate the dashboard JSON based on RetractionDate (notice year).
    
    Args:
        csv_file_path: Path to the input CSV file
        output_json_path: Path to the output JSON file
        publication_file: Optional path to a file containing publication counts per country
        min_year: Optional minimum retraction year to include (inclusive)
        max_year: Optional maximum retraction year to include (inclusive)
    """
    print(f"Reading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    print(f"Loaded {len(df)} records")
    
    # Filter by RetractionNature == "Retraction"
    initial_count = len(df)
    df = df[df['RetractionNature'] == 'Retraction']
    filtered_count = len(df)
    print(f"Filtered to {filtered_count} records (from {initial_count}) where RetractionNature == 'Retraction'")
    
    # Parse RetractionDate and extract year
    print("Parsing RetractionDate...")
    df['retraction_year'] = df['RetractionDate'].apply(parse_retraction_date)
    
    # Filter by year range if specified (for numbered files), otherwise include all records
    if min_year is not None or max_year is not None:
        initial_count = len(df)
        if min_year is not None:
            df = df[df['retraction_year'] >= min_year]
        if max_year is not None:
            df = df[df['retraction_year'] <= max_year]
        filtered_count = len(df)
        year_range = f"{min_year or 'any'}-{max_year or 'any'}"
        print(f"Filtered to {filtered_count} records (from {initial_count}) based on RetractionDate {year_range}")
    else:
        print(f"Processing all {len(df)} records (no date filter for base file)")
    if max_year is not None:
        print(f"  Maximum year: {max_year}")
    
    # Count records with valid retraction dates
    valid_dates = df['retraction_year'].notna().sum()
    print(f"Records with valid RetractionDate: {valid_dates}/{len(df)}")
    
    # Show year distribution
    if valid_dates > 0:
        year_counts = df['retraction_year'].value_counts().sort_index()
        print(f"Retraction year range: {year_counts.index.min()} - {year_counts.index.max()}")
        print(f"Top retraction years:")
        for year, count in year_counts.head(10).items():
            print(f"  {int(year)}: {count} retractions")
    
    # Load publication data from scimago_combined.csv (default)
    publication_data, scimago_countries = load_publication_data(publication_file)
    country_matches = {}  # Track fuzzy matches
    
    if publication_data:
        print(f"Loaded publication data for {len(publication_data)} countries")
    else:
        print("Warning: No publication data available. Retraction rates will be set to 0.0")
        scimago_countries = []
    
    # Load classification files from classification folder
    classification_keywords = load_classification_files()
    use_file_classification = any(classification_keywords.values())
    
    if use_file_classification:
        print("Using classification files from classification/ folder for categorization")
    else:
        print("Warning: No classification files found. Using default keyword-based classification")
    
    # Initialize country statistics
    country_stats = defaultdict(lambda: {
        'alterations': 0,
        'research': 0,
        'integrity': 0,
        'supplemental': 0,
        'system': 0,
        'total': 0,
        'total_from_1996': 0  # Count of retractions from 1996 onwards (based on RetractionDate)
    })
    
    # Process each row
    skipped_no_date = 0
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(f"Processing row {idx}/{len(df)}")
        
        # Skip if no valid retraction date
        if pd.isna(row.get('retraction_year')):
            skipped_no_date += 1
            continue
        
        # Get countries (can be multiple, separated by semicolons)
        countries_str = str(row.get('Country', ''))
        if pd.isna(countries_str) or countries_str.lower() in ['unknown', 'nan', '']:
            continue
        
        # Split countries
        countries = [c.strip() for c in countries_str.split(';') if c.strip()]
        
        # Classify the retraction
        # Always try to use classification files if available, fallback to default
        if use_file_classification:
            classifications = classify_with_files(row, classification_keywords)
        else:
            classifications = classify_retraction(row)
        
        # Update statistics for each country
        # Check if this record is from 1996 onwards for retraction rate calculation
        retraction_year = row.get('retraction_year')
        is_from_1996 = pd.notna(retraction_year) and retraction_year >= 1996
        
        for country in countries:
            if country:
                country_stats[country]['total'] += 1
                # Count retractions from 1996 onwards separately (based on RetractionDate)
                if is_from_1996:
                    country_stats[country]['total_from_1996'] += 1
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
    
    if skipped_no_date > 0:
        print(f"Skipped {skipped_no_date} records without valid RetractionDate")
    
    print(f"Processed {len(country_stats)} countries")
    
    # Convert to list format and calculate retraction_rate
    result = []
    for country, stats in country_stats.items():
        # Total retractions = unique record count (all records, including before 1996)
        total_retractions = stats['total']
        
        # Total retractions from 1996 onwards (for retraction rate calculation)
        total_retractions_from_1996 = stats['total_from_1996']
        
        # Get total publications for this country (1996-2024)
        total_publications = publication_data.get(country)
        
        # If no publication data found, try fuzzy matching
        if (total_publications is None or total_publications == 0) and scimago_countries:
            matched_country = find_similar_country(country, scimago_countries)
            if matched_country:
                total_publications = publication_data.get(matched_country)
                if total_publications:
                    country_matches[country] = matched_country
                    print(f"Matched '{country}' -> '{matched_country}' for publication data")
        
        # Calculate retraction_rate: (total_retractions_from_1996 / total_publications) * 1000
        retraction_rate = calculate_retraction_rate(total_retractions_from_1996, total_publications)
        
        result.append({
            'country': country,
            'alterations': stats['alterations'],
            'research': stats['research'],
            'integrity': stats['integrity'],
            'supplemental': stats['supplemental'],
            'system': stats['system'],
            'total': total_retractions,  # All retractions (including before 1996)
            'total_from_1996': total_retractions_from_1996,  # Retractions from 1996 onwards
            'total_publications': int(total_publications) if total_publications else 0,  # Total publications (1996-2024)
            'retraction_rate': retraction_rate,  # (total_from_1996 / total_publications) * 1000
            'country_flag': get_country_flag_path(country)
        })
    
    # Save country matches to file (matches should be the same as from original date script)
    if country_matches:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        matches_file = os.path.join(project_root, 'country_matches.txt')
        # Read existing matches if file exists
        existing_matches = {}
        if os.path.exists(matches_file):
            try:
                with open(matches_file, 'r') as f:
                    for line in f:
                        if '->' in line and not line.startswith('=') and not line.startswith('Country'):
                            parts = line.strip().split(' -> ')
                            if len(parts) == 2:
                                existing_matches[parts[0]] = parts[1]
            except:
                pass
        
        # Merge matches
        all_matches = {**existing_matches, **country_matches}
        
        with open(matches_file, 'w') as f:
            f.write("Country Name Matches (Retraction Watch -> Scimago)\n")
            f.write("=" * 60 + "\n\n")
            for retraction_country, scimago_country in sorted(all_matches.items()):
                f.write(f"{retraction_country} -> {scimago_country}\n")
        print(f"\nSaved {len(all_matches)} country matches to {matches_file}")
    
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
    json_file = 'dashboard_table_by_retraction_date.json'
    publication_file = None
    min_year = None
    max_year = None
    
    # Parse command line arguments
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--min-year' and i + 1 < len(sys.argv):
            min_year = int(sys.argv[i + 1])
            i += 2
        elif arg == '--max-year' and i + 1 < len(sys.argv):
            max_year = int(sys.argv[i + 1])
            i += 2
        elif i == 1:
            csv_file = arg
            i += 1
        elif i == 2:
            json_file = arg
            i += 1
        elif i == 3:
            publication_file = arg
            i += 1
        else:
            i += 1
    
    process_csv_to_json_by_retraction_date(csv_file, json_file, publication_file, min_year, max_year)

