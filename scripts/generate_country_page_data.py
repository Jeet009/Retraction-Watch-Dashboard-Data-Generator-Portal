import pandas as pd
import json
import os
import re
from collections import defaultdict
from datetime import datetime

def parse_original_paper_date(date_str):
    """Parse OriginalPaperDate and return year as integer."""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ['nan', 'none', '']:
        return None
    
    # Try different date formats
    formats = [
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.split()[0] if ' ' in date_str else date_str, fmt)
            return dt.year
        except:
            continue
    
    # If all formats fail, try to extract year from string
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        return int(year_match.group())
    
    return None

def parse_retraction_date(date_str):
    """Parse RetractionDate and return year as integer."""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ['nan', 'none', '']:
        return None
    
    # Try different date formats
    formats = [
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.split()[0] if ' ' in date_str else date_str, fmt)
            return dt.year
        except:
            continue
    
    # If all formats fail, try to extract year from string
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        return int(year_match.group())
    
    return None

def parse_domains(subject_str):
    """Parse Subject column to extract domain codes like BLS, HSC, PHY, etc."""
    if pd.isna(subject_str):
        return []
    
    subject_str = str(subject_str)
    # Pattern: (CODE) Description
    pattern = r'\(([A-Z/]+)\)'
    domains = re.findall(pattern, subject_str)
    # Clean up domain codes (remove trailing semicolons, etc.)
    domains = [d.strip() for d in domains if d.strip()]
    return domains

def apply_retraction_classification(df):
    """Apply retraction_classification.py logic to add a 'mark' column."""
    df['mark'] = None
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    classification_folder = os.path.join(project_root, 'classification')
    
    list_of_marks = ['Supplemental', 'System', 'Research', 'Integrity', 'Serious']
    
    for mark in list_of_marks:
        file_path = os.path.join(classification_folder, mark + '.txt')
        
        if not os.path.exists(file_path):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file if line.strip()]
            
            if not lines:
                continue
            
            escaped_lines = [re.escape(line) for line in lines]
            pattern = '|'.join(escaped_lines)
            
            filtered_df = df[df['Reason'].str.contains(pattern, case=False, na=False, regex=True)]
            df.loc[filtered_df.index, 'mark'] = mark
            
        except Exception as e:
            print(f"Warning: Could not process {file_path}: {e}")
    
    # Assign unmarked records to 'Research'
    if df['mark'].isna().sum() > 0:
        df.loc[df['mark'].isna(), 'mark'] = 'Research'
    
    return df

def get_country_flag_path(country):
    """Get the path to the country flag SVG."""
    country_name = country.replace(' ', '_')
    return f"/country_flags/{country_name}.svg"

def load_publication_data(publication_file=None):
    """Load publication data from scimago_combined.csv."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if publication_file is None:
        publication_file = os.path.join(project_root, 'data', 'scimago_combined.csv')
    
    publication_data = {}
    yearly_publication_data = {}
    scimago_countries = []
    
    if os.path.exists(publication_file):
        print(f"Loading publication data from: {publication_file}")
        pub_df = pd.read_csv(publication_file)
        
        for _, row in pub_df.iterrows():
            country = row['Country']
            scimago_countries.append(country)
            
            total = 0
            yearly = {}
            for year in range(1996, 2025):
                year_str = str(year)
                if year_str in pub_df.columns:
                    count = row.get(year_str, 0)
                    if pd.notna(count):
                        count = int(count)
                        total += count
                        yearly[year_str] = count
            
            publication_data[country] = total
            yearly_publication_data[country] = yearly
    else:
        print(f"Warning: Publication file not found: {publication_file}")
    
    return publication_data, yearly_publication_data, scimago_countries

def calculate_retraction_rate(total_retractions, total_publications=None):
    """Calculate retraction rate per 1000 publications."""
    if total_publications is None or total_publications == 0:
        return 0.0
    else:
        return round((total_retractions / total_publications) * 1000, 4)

def generate_country_page_data(csv_file_path, output_folder):
    """Generate country page data files for all countries."""
    print(f"Reading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    print(f"Loaded {len(df)} records")
    
    # Filter by RetractionNature == "Retraction"
    df = df[df['RetractionNature'] == 'Retraction']
    print(f"Filtered to {len(df)} records where RetractionNature == 'Retraction'")
    
    # Apply classification
    print("Applying retraction classification...")
    df = apply_retraction_classification(df)
    
    # Parse dates
    print("Parsing dates...")
    df['original_paper_year'] = df['OriginalPaperDate'].apply(parse_original_paper_date)
    df['retraction_year'] = df['RetractionDate'].apply(parse_retraction_date)
    
    # Parse domains
    print("Parsing domains...")
    df['domains'] = df['Subject'].apply(parse_domains)
    
    # Load publication data
    publication_data, yearly_publication_data, scimago_countries = load_publication_data()
    
    # Structure to store country data
    # country_data[country] = {
    #   'yearly_retractions': {year: count},
    #   'notice_yearly_retractions': {year: count},
    #   'yearly_data': {year: {total, marks: {...}, domain: {...}}},
    #   'notice_yearly_data': {year: {total, marks: {...}, domain: {...}}},
    #   'collaborations': {country: count},
    #   'notice_collaborations': {country: count}
    # }
    country_data = defaultdict(lambda: {
        'yearly_retractions': defaultdict(int),
        'notice_yearly_retractions': defaultdict(int),
        'yearly_data': defaultdict(lambda: {
            'total': 0,
            'marks': defaultdict(int),
            'domain': defaultdict(int)
        }),
        'notice_yearly_data': defaultdict(lambda: {
            'total': 0,
            'marks': defaultdict(int),
            'domain': defaultdict(int)
        }),
        'collaborations': defaultdict(int),
        'notice_collaborations': defaultdict(int)
    })
    
    # Mark to category mapping
    mark_to_category = {
        'Supplemental': 'supplemental',
        'System': 'system',
        'Research': 'research',
        'Integrity': 'researcher_integrity',  # Note: using 'researcher_integrity' to match example
        'Serious': 'alterations'
    }
    
    print("Processing records...")
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(f"Processing row {idx}/{len(df)}")
        
        # Get countries
        countries_str = str(row.get('Country', ''))
        if pd.isna(countries_str) or countries_str.lower() in ['unknown', 'nan', '']:
            continue
        
        countries = [c.strip() for c in countries_str.split(';') if c.strip()]
        if not countries:
            continue
        
        # Get classification mark
        mark = row.get('mark')
        category = mark_to_category.get(mark, 'research')
        
        # Get domains
        domains = row.get('domains', [])
        if not domains:
            domains = ['']  # Empty domain
        
        # Get years
        original_year = row.get('original_paper_year')
        retraction_year = row.get('retraction_year')
        
        # Process for each country
        for country in countries:
            # Yearly data (based on OriginalPaperDate)
            if pd.notna(original_year):
                year_str = str(int(original_year))
                country_data[country]['yearly_retractions'][year_str] += 1
                country_data[country]['yearly_data'][year_str]['total'] += 1
                country_data[country]['yearly_data'][year_str]['marks'][category] += 1
                for domain in domains:
                    country_data[country]['yearly_data'][year_str]['domain'][domain] += 1
            
            # Notice yearly data (based on RetractionDate)
            if pd.notna(retraction_year):
                year_str = str(int(retraction_year))
                country_data[country]['notice_yearly_retractions'][year_str] += 1
                country_data[country]['notice_yearly_data'][year_str]['total'] += 1
                country_data[country]['notice_yearly_data'][year_str]['marks'][category] += 1
                for domain in domains:
                    country_data[country]['notice_yearly_data'][year_str]['domain'][domain] += 1
            
            # Collaborations (other countries in the same record)
            for other_country in countries:
                if other_country != country:
                    country_data[country]['collaborations'][other_country] += 1
                    country_data[country]['notice_collaborations'][other_country] += 1
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    print(f"\nGenerating country page data files...")
    
    # Generate JSON for each country
    for country, data in country_data.items():
        # Calculate yearly retraction rates (based on OriginalPaperDate)
        yearly_rates = {}
        country_yearly_pubs = yearly_publication_data.get(country, {})
        
        for year in range(1996, 2025):
            year_str = str(year)
            retractions = data['yearly_retractions'].get(year_str, 0)
            publications = country_yearly_pubs.get(year_str, 0)
            rate = calculate_retraction_rate(retractions, publications)
            if rate > 0 or retractions > 0:
                yearly_rates[year_str] = rate
        
        # Calculate notice yearly retraction rates (based on RetractionDate)
        notice_yearly_rates = {}
        for year in range(1996, 2025):
            year_str = str(year)
            retractions = data['notice_yearly_retractions'].get(year_str, 0)
            publications = country_yearly_pubs.get(year_str, 0)
            rate = calculate_retraction_rate(retractions, publications)
            if rate > 0 or retractions > 0:
                notice_yearly_rates[year_str] = rate
        
        # Calculate average rate
        total_retractions_from_1996 = sum(data['yearly_retractions'].get(str(y), 0) for y in range(1996, 2025))
        total_publications = publication_data.get(country, 0)
        average_rate = calculate_retraction_rate(total_retractions_from_1996, total_publications)
        
        # Build yearly data structure
        years_data = {}
        for year in sorted(data['yearly_data'].keys(), reverse=True):
            year_data = data['yearly_data'][year]
            years_data[year] = {
                'total': year_data['total'],
                'marks': dict(year_data['marks']),
                'domain': dict(year_data['domain'])
            }
        
        # Build notice yearly data structure
        notice_years_data = {}
        for year in sorted(data['notice_yearly_data'].keys(), reverse=True):
            year_data = data['notice_yearly_data'][year]
            notice_years_data[year] = {
                'total': year_data['total'],
                'marks': dict(year_data['marks']),
                'domain': dict(year_data['domain'])
            }
        
        # Build yearly retractions counts (not rates)
        yearly_retractions = {year_str: data['yearly_retractions'].get(year_str, 0) 
                              for year_str in [str(y) for y in range(1996, 2025)] 
                              if data['yearly_retractions'].get(year_str, 0) > 0}
        
        notice_yearly_retractions = {year_str: data['notice_yearly_retractions'].get(year_str, 0) 
                                     for year_str in [str(y) for y in range(1996, 2025)] 
                                     if data['notice_yearly_retractions'].get(year_str, 0) > 0}
        
        # Build output JSON
        output_data = {
            'retraction_rate_data': {
                'country': country,
                'yearly_rates': yearly_rates,
                'notice_yearly_rates': notice_yearly_rates,
                'average_rate': average_rate,
                'yearly_retractions': yearly_retractions,
                'notice_yearly_retractions': notice_yearly_retractions
            },
            'domainwise_data': {
                'country': country,
                'total_retractions': sum(data['yearly_retractions'].values()),
                'years': years_data,
                'notice_years': notice_years_data,
                'collaborations': dict(sorted(data['collaborations'].items(), key=lambda x: x[1], reverse=True)),
                'notice_collaborations': dict(sorted(data['notice_collaborations'].items(), key=lambda x: x[1], reverse=True))
            },
            'country_flag': get_country_flag_path(country)
        }
        
        # Write to file
        country_filename = country.replace(' ', '_').replace('/', '_')
        output_path = os.path.join(output_folder, f"{country_filename}_CountryPageData.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        if len(country_data) % 10 == 0:
            print(f"Generated {len(country_data)} country files...")
    
    print(f"\nSuccessfully generated {len(country_data)} country page data files in {output_folder}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    csv_file = os.path.join(project_root, 'data', 'retraction_watch.csv')
    output_folder = os.path.join(project_root, 'country_data')
    
    generate_country_page_data(csv_file, output_folder)

