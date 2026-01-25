#!/bin/bash

# Configuration
PROJECT_ROOT="/Users/jeetmukherjee/Desktop/PostPub/Development/postpub-backend-pipeline"
SOURCES_DIR="$PROJECT_ROOT/sources"
DATA_DIR="$PROJECT_ROOT/data"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
REPO_URL="https://gitlab.com/crossref/retraction-watch-data.git"

# Ensure directories exist
mkdir -p "$SOURCES_DIR"
mkdir -p "$DATA_DIR"

# 1. Update/Clone the repository
echo "Updating data source from GitLab..."
if [ -d "$SOURCES_DIR/retraction-watch-data" ]; then
    cd "$SOURCES_DIR/retraction-watch-data"
    git pull
else
    cd "$SOURCES_DIR"
    git clone "$REPO_URL"
fi

# 2. Copy the CSV file
echo "Copying retraction_watch.csv to data directory..."
# Verify file exists in the repo structure
if [ -f "$SOURCES_DIR/retraction-watch-data/retraction_watch.csv" ]; then
    cp "$SOURCES_DIR/retraction-watch-data/retraction_watch.csv" "$DATA_DIR/retraction_watch.csv"
else
    # Sometimes repos might have data in a subdir or names might differ, check if it's named differently
    # Based on user input it is retraction_watch.csv
    # If not found, try finding it
    FOUND_CSV=$(find "$SOURCES_DIR/retraction-watch-data" -name "retraction_watch.csv" | head -n 1)
    if [ ! -z "$FOUND_CSV" ]; then
        cp "$FOUND_CSV" "$DATA_DIR/retraction_watch.csv"
    else
        echo "Error: retraction_watch.csv not found in the repository."
        exit 1
    fi
fi

# 3. Run processing scripts
echo "Running processing scripts..."
cd "$PROJECT_ROOT"

# Set up output directories just in case
mkdir -p "$PROJECT_ROOT/dashboard_outputs/years"
mkdir -p "$PROJECT_ROOT/dashboard_outputs/notice_years"

# Activate venv if it exists, otherwise assume python is in path
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Generate Dashboard (OriginalPaperDate)
echo "Generating dashboard (OriginalPaperDate)..."
python3 scripts/generate_dashboard_json.py data/retraction_watch.csv dashboard_outputs/years/dashboard_table.json

# Generate Dashboard (RetractionDate)
echo "Generating dashboard (RetractionDate)..."
python3 scripts/generate_dashboard_json_by_retraction_date.py data/retraction_watch.csv dashboard_outputs/notice_years/dashboard_table.json

# Generate All Filtered Dashboards
echo "Generating filtered dashboards..."
python3 scripts/generate_filtered_dashboards.py data/retraction_watch.csv dashboard_outputs

# Generate Country Page Data
echo "Generating country page data..."
python3 scripts/generate_country_page_data.py

# Generate Race CSV (assuming user wants this too)
echo "Generating race CSV..."
python3 create_race_csv.py

echo "All processing complete!"
