# Dashboard Output Files

This folder contains filtered dashboard JSON files organized by date type.

## Folder Structure

### `years/`
Contains dashboard files filtered by **OriginalPaperDate** (when the paper was originally published).

- `dashboard_table.json` - All data from 1996 onwards
- `dashboard_table_1.json` - Last 1 year (2025)
- `dashboard_table_2.json` - Last 2 years (2024-2025)
- `dashboard_table_3.json` - Last 3 years (2023-2025)
- `dashboard_table_4.json` - Last 4 years (2022-2025)
- `dashboard_table_5.json` - Last 5 years (2021-2025)
- `dashboard_table_6.json` - Last 6 years (2020-2025)
- `dashboard_table_7.json` - Last 7 years (2019-2025)
- `dashboard_table_8.json` - Last 8 years (2018-2025)
- `dashboard_table_9.json` - Last 9 years (2017-2025)
- `dashboard_table_10.json` - Last 10 years (2016-2025)

### `notice_years/`
Contains dashboard files filtered by **RetractionDate** (when the retraction notice was issued).

- `dashboard_table.json` - All data from 1996 onwards
- `dashboard_table_1.json` - Last 1 year (2025)
- `dashboard_table_2.json` - Last 2 years (2024-2025)
- `dashboard_table_3.json` - Last 3 years (2023-2025)
- `dashboard_table_4.json` - Last 4 years (2022-2025)
- `dashboard_table_5.json` - Last 5 years (2021-2025)
- `dashboard_table_6.json` - Last 6 years (2020-2025)
- `dashboard_table_7.json` - Last 7 years (2019-2025)
- `dashboard_table_8.json` - Last 8 years (2018-2025)
- `dashboard_table_9.json` - Last 9 years (2017-2025)
- `dashboard_table_10.json` - Last 10 years (2016-2025)

## File Format

Each JSON file contains an array of country objects with the following structure:

```json
{
  "country": "Country Name",
  "alterations": 0,
  "research": 0,
  "integrity": 0,
  "supplemental": 0,
  "system": 0,
  "total": 0,
  "retraction_rate": 0.0,
  "country_flag": "/country_flags/Country_Name.svg"
}
```

## Regenerating Files

To regenerate all filtered dashboard files, run:

```bash
python generate_filtered_dashboards.py retraction_watch.csv dashboard_outputs
```

## Notes

- All files filter data from 1996 onwards (earliest year in Scimago publication data)
- Retraction rates are calculated using: `(total_retractions / total_publications) * 1000`
- Total retractions = sum of all categories (Supplemental + System + Research + Integrity + Serious/Alterations)
- Classification uses keywords from the `classification/` folder

