import os
import sys
from datetime import datetime
import sys
import os

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from generate_dashboard_json import process_csv_to_json, parse_original_paper_date
from generate_dashboard_json_by_retraction_date import process_csv_to_json_by_retraction_date, parse_retraction_date
import pandas as pd

def get_latest_year_from_data(csv_file, date_column):
    """
    Get the latest year from the CSV data for a given date column.
    """
    print(f"Determining latest year from {date_column}...")
    df = pd.read_csv(csv_file)
    
    if date_column == 'OriginalPaperDate':
        df['year'] = df[date_column].apply(parse_original_paper_date)
    elif date_column == 'RetractionDate':
        df['year'] = df[date_column].apply(parse_retraction_date)
    else:
        return None
    
    valid_years = df['year'].dropna()
    if len(valid_years) > 0:
        latest_year = int(valid_years.max())
        print(f"Latest year found: {latest_year}")
        return latest_year
    return None

def generate_filtered_dashboards(csv_file=None, base_output_dir='dashboard_outputs'):
    """
    Generate filtered dashboard JSON files for last 1-10 years.
    Creates two folders: one for OriginalPaperDate (years) and one for RetractionDate (notice_years).
    """
    # Default CSV path
    if csv_file is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        csv_file = os.path.join(project_root, 'data', 'retraction_watch.csv')
        if not os.path.exists(csv_file):
            csv_file = 'retraction_watch.csv'
    
    # Ensure output directory is relative to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    base_output_dir = os.path.join(project_root, base_output_dir)
    
    # Determine latest year from data
    latest_year_original = get_latest_year_from_data(csv_file, 'OriginalPaperDate')
    latest_year_retraction = get_latest_year_from_data(csv_file, 'RetractionDate')
    
    if latest_year_original is None:
        print("Error: Could not determine latest year from OriginalPaperDate")
        return
    
    if latest_year_retraction is None:
        print("Error: Could not determine latest year from RetractionDate")
        return
    
    # Create output directories
    years_dir = os.path.join(base_output_dir, 'years')
    notice_years_dir = os.path.join(base_output_dir, 'notice_years')
    
    os.makedirs(years_dir, exist_ok=True)
    os.makedirs(notice_years_dir, exist_ok=True)
    
    print(f"\nCreating filtered dashboards...")
    print(f"Years folder: {years_dir}")
    print(f"Notice years folder: {notice_years_dir}\n")
    
    # Generate files for OriginalPaperDate (years)
    print("=" * 60)
    print("Generating files based on OriginalPaperDate (years)")
    print("=" * 60)
    
    for years in range(1, 11):
        min_year = latest_year_original - years + 1
        output_file = os.path.join(years_dir, f'dashboard_table_{years}.json')
        
        print(f"\nGenerating dashboard_table_{years}.json (years {min_year}-{latest_year_original})...")
        
        # We need to modify the process_csv_to_json to accept min_year parameter
        # For now, let's create a modified version that filters by year
        generate_filtered_by_original_date(csv_file, output_file, min_year, latest_year_original)
    
    # Generate base file (all data, no date filter)
    print(f"\nGenerating dashboard_table.json (all data, no date filter)...")
    base_output_file = os.path.join(years_dir, 'dashboard_table.json')
    process_csv_to_json(csv_file, base_output_file, None, None, None)
    
    # Generate files for RetractionDate (notice_years)
    print("\n" + "=" * 60)
    print("Generating files based on RetractionDate (notice_years)")
    print("=" * 60)
    
    for years in range(1, 11):
        min_year = latest_year_retraction - years + 1
        output_file = os.path.join(notice_years_dir, f'dashboard_table_{years}.json')
        
        print(f"\nGenerating dashboard_table_{years}.json (notice years {min_year}-{latest_year_retraction})...")
        process_csv_to_json_by_retraction_date(csv_file, output_file, None, min_year, latest_year_retraction)
    
    # Generate base file (all data, no date filter)
    print(f"\nGenerating dashboard_table.json (all data, no date filter)...")
    base_output_file = os.path.join(notice_years_dir, 'dashboard_table.json')
    process_csv_to_json_by_retraction_date(csv_file, base_output_file, None, None, None)
    
    print("\n" + "=" * 60)
    print("All filtered dashboards generated successfully!")
    print(f"Years folder: {years_dir}")
    print(f"Notice years folder: {notice_years_dir}")
    print("=" * 60)

def generate_filtered_by_original_date(csv_file_path, output_json_path, min_year, max_year):
    """
    Generate dashboard JSON filtered by OriginalPaperDate year range.
    This is a modified version of process_csv_to_json that accepts year filters.
    """
    # Import necessary functions (from same directory)
    from generate_dashboard_json import (
        apply_retraction_classification,
        get_country_flag_path, load_publication_data,
        calculate_retraction_rate, parse_original_paper_date,
        find_similar_country, load_yearly_publication_data_from_scimago
    )
    from collections import defaultdict
    
    print(f"Reading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    print(f"Loaded {len(df)} records")
    
    # Filter by RetractionNature == "Retraction"
    initial_count = len(df)
    df = df[df['RetractionNature'] == 'Retraction']
    filtered_count = len(df)
    print(f"Filtered to {filtered_count} records (from {initial_count}) where RetractionNature == 'Retraction'")
    
    # Parse OriginalPaperDate and filter to year range
    print(f"Parsing OriginalPaperDate and filtering to {min_year}-{max_year}...")
    df['original_paper_year'] = df['OriginalPaperDate'].apply(parse_original_paper_date)
    
    # Filter to year range
    initial_count = len(df)
    df = df[(df['original_paper_year'] >= min_year) & (df['original_paper_year'] <= max_year)]
    filtered_count = len(df)
    print(f"Filtered to {filtered_count} records (from {initial_count}) based on OriginalPaperDate {min_year}-{max_year}")
    
    # Load publication data from scimago_combined.csv (default)
    publication_data, scimago_countries = load_publication_data(None)
    country_matches = {}  # Track fuzzy matches
    
    # Load yearly publication data for yearly retraction rate calculation
    yearly_publication_data, _ = load_yearly_publication_data_from_scimago()
    
    if publication_data:
        print(f"Loaded publication data for {len(publication_data)} countries")
    else:
        print("Warning: No publication data available. Retraction rates will be set to 0.0")
        scimago_countries = []
    
    # Apply retraction_classification.py logic to add 'mark' column
    print("Applying retraction classification (same as retraction_classification.py)...")
    df = apply_retraction_classification(df)
    
    # Check if we have any marked records
    if df['mark'].isna().all():
        print("Warning: No records were classified. Cannot generate dashboard.")
        return []
    
    # Initialize country statistics
    country_stats = defaultdict(lambda: {
        'alterations': 0,
        'research': 0,
        'integrity': 0,
        'supplemental': 0,
        'system': 0,
        'total': 0,
        'total_from_1996': 0,  # Count of retractions from 1996 onwards
        'yearly_retractions': defaultdict(int)  # Track retractions per year
    })
    
    # Map mark to category
    mark_to_category = {
        'Supplemental': 'supplemental',
        'System': 'system',
        'Research': 'research',
        'Integrity': 'integrity',
        'Serious': 'alterations'
    }
    
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
        
        # Get mark from the DataFrame
        mark = row.get('mark')
        category = mark_to_category.get(mark) if pd.notna(mark) else None
        
        # Update statistics for each country
        # Check if this record is from 1996 onwards for retraction rate calculation
        is_from_1996 = row.get('original_paper_year', 0) >= 1996 if pd.notna(row.get('original_paper_year')) else False
        paper_year = row.get('original_paper_year')
        year_str = str(int(paper_year)) if pd.notna(paper_year) and 1996 <= paper_year <= 2024 else None
        
        for country in countries:
            if country:
                country_stats[country]['total'] += 1
                # Count retractions from 1996 onwards separately
                if is_from_1996:
                    country_stats[country]['total_from_1996'] += 1
                    # Track retractions per year
                    if year_str:
                        country_stats[country]['yearly_retractions'][year_str] += 1
                
                # Count in only ONE category based on mark (not multiple)
                if category:
                    country_stats[country][category] += 1
    
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
        
        # Calculate yearly retraction rates
        yearly_retraction_rates = {}
        country_yearly_pubs = yearly_publication_data.get(country)
        
        # If no yearly publication data found, try fuzzy matching
        if (country_yearly_pubs is None or not country_yearly_pubs) and scimago_countries:
            matched_country = find_similar_country(country, scimago_countries)
            if matched_country:
                country_yearly_pubs = yearly_publication_data.get(matched_country)
        
        # Calculate retraction rate for each year (1996-2024)
        for year in range(1996, 2025):
            year_str = str(year)
            retractions_in_year = stats['yearly_retractions'].get(year_str, 0)
            publications_in_year = country_yearly_pubs.get(year_str, 0) if country_yearly_pubs else 0
            yearly_rate = calculate_retraction_rate(retractions_in_year, publications_in_year)
            if yearly_rate > 0 or retractions_in_year > 0:  # Include year if there are retractions or rate > 0
                yearly_retraction_rates[year_str] = yearly_rate
        
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
            'yearly_retraction_rates': yearly_retraction_rates,  # Dict with year -> retraction_rate
            'country_flag': get_country_flag_path(country)
        })
    
    # Sort by total (descending)
    result.sort(key=lambda x: x['total'], reverse=True)
    
    # Write to JSON file
    print(f"Writing JSON to: {output_json_path}")
    import json
    with open(output_json_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Successfully generated JSON file with {len(result)} countries")
    return result

if __name__ == '__main__':
    csv_file = None
    output_dir = 'dashboard_outputs'
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    generate_filtered_dashboards(csv_file, output_dir)

