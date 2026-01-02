# Quick Start Guide

## Starting the Web Application

1. **Install dependencies** (if not already installed):
```bash
pip install -r requirements.txt
```

2. **Start the server**:
```bash
python app.py
```

Or use the startup script:
```bash
./run.sh
```

3. **Access the application**:
Open your browser and go to: `http://localhost:5000`

## Using the Web Interface

### Upload CSV File
1. Click on the upload area or drag and drop a CSV file
2. The file should be named with "retraction" or "watch" in the filename
3. Click "Process File" to generate dashboard JSON files
4. Wait for processing to complete (may take a few minutes)

### View Files
1. Use the tabs to switch between:
   - **Years**: Files based on OriginalPaperDate
   - **Notice Years**: Files based on RetractionDate
2. Click "View" to see the JSON content in a modal
3. Click "Download" to download the JSON file

### File Viewer Features
- View formatted JSON with syntax highlighting
- Copy JSON to clipboard
- Download the file
- See country count statistics

## File Organization

- **data/**: CSV input files
- **scripts/**: Python processing scripts
- **dashboard_outputs/**: Generated JSON files
  - **years/**: Based on OriginalPaperDate (11 files)
  - **notice_years/**: Based on RetractionDate (11 files)

## Command Line Usage

You can also run scripts directly from the command line:

```bash
# Generate single dashboard
python scripts/generate_dashboard_json.py data/retraction_watch.csv dashboard_outputs/years/dashboard_table.json

# Generate all filtered dashboards
python scripts/generate_filtered_dashboards.py data/retraction_watch.csv dashboard_outputs
```

