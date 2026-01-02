# Retraction Watch Dashboard Generator

A web application for processing retraction watch CSV files and generating dashboard JSON files with country-level statistics.

## Project Structure

```
postpub-backend-pipeline/
├── app.py                      # Flask web application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── classification/             # Classification keyword files
│   ├── Integrity.txt
│   ├── Research.txt
│   ├── Serious.txt
│   ├── Supplemental.txt
│   └── System.txt
│
├── data/                       # CSV data files
│   ├── retraction_watch.csv
│   └── scimago_combined.csv
│
├── scripts/                    # Python processing scripts
│   ├── generate_dashboard_json.py
│   ├── generate_dashboard_json_by_retraction_date.py
│   ├── generate_filtered_dashboards.py
│   └── retraction_classification.py
│
├── dashboard_outputs/          # Generated JSON files
│   ├── README.md
│   ├── years/                  # Based on OriginalPaperDate
│   │   ├── dashboard_table.json
│   │   ├── dashboard_table_1.json (last 1 year)
│   │   └── ... (2-10 years)
│   └── notice_years/           # Based on RetractionDate
│       ├── dashboard_table.json
│       ├── dashboard_table_1.json (last 1 year)
│       └── ... (2-10 years)
│
├── templates/                  # HTML templates
│   └── index.html
│
└── static/                     # Static assets
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure all data files are in the `data/` folder:
   - `retraction_watch.csv`
   - `scimago_combined.csv`

3. Ensure classification files are in the `classification/` folder

## Running the Web Application

Start the Flask server:
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Features

### Web Interface
- **Upload CSV Files**: Drag and drop or click to upload retraction watch CSV files
- **View Files**: Browse and view all generated dashboard JSON files
- **Download Files**: Download any dashboard JSON file
- **File Viewer**: View JSON content with syntax highlighting
- **Two Views**: 
  - Years (based on OriginalPaperDate)
  - Notice Years (based on RetractionDate)

### Command Line Scripts

#### Generate Dashboard (OriginalPaperDate)
```bash
python scripts/generate_dashboard_json.py data/retraction_watch.csv dashboard_outputs/years/dashboard_table.json
```

#### Generate Dashboard (RetractionDate)
```bash
python scripts/generate_dashboard_json_by_retraction_date.py data/retraction_watch.csv dashboard_outputs/notice_years/dashboard_table.json
```

#### Generate All Filtered Dashboards
```bash
python scripts/generate_filtered_dashboards.py data/retraction_watch.csv dashboard_outputs
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/files` - List all available dashboard JSON files
- `GET /api/view/<folder>/<filename>` - View a specific JSON file
- `GET /api/download/<folder>/<filename>` - Download a JSON file
- `POST /api/upload` - Upload and process a CSV file
- `POST /api/process` - Process an existing CSV file

## Dashboard JSON Format

Each JSON file contains an array of country objects:

```json
{
  "country": "United States",
  "alterations": 2722,
  "research": 3623,
  "integrity": 1655,
  "supplemental": 3874,
  "system": 1226,
  "total": 13100,
  "retraction_rate": 0.8962,
  "country_flag": "/country_flags/United_States.svg"
}
```

## Categories

- **alterations**: Duplication and authorship issues (from Serious.txt)
- **research**: Research-related issues (from Research.txt)
- **integrity**: Integrity and misconduct issues (from Integrity.txt)
- **supplemental**: Supplemental materials and corrections (from Supplemental.txt)
- **system**: System and process issues (from System.txt)

## Retraction Rate Calculation

Retraction rate = (total_retractions / total_publications) * 1000

Where:
- `total_retractions` = sum of all categories
- `total_publications` = sum of publications from 1996-2024 (from scimago_combined.csv)

## Notes

- All data is filtered to include only records from 1996 onwards
- Classification uses keywords from the `classification/` folder
- A single retraction can belong to multiple categories
- The `total` field represents the sum of all category counts
