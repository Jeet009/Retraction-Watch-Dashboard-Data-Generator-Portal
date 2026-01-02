# Vercel Deployment Guide

## Setup Vercel Blob Storage

1. **Create Blob Store in Vercel:**
   - Go to your Vercel dashboard
   - Navigate to Storage → Create Database/Store
   - Select "Blob" and create a new blob store
   - Note the store name

2. **Get Blob Token:**
   - In Vercel dashboard, go to your project settings
   - Navigate to Environment Variables
   - Add `BLOB_READ_WRITE_TOKEN` with your blob store token
   - Or use Vercel CLI: `vercel env add BLOB_READ_WRITE_TOKEN`

3. **Deploy:**
   ```bash
   vercel deploy
   ```

## How It Works

- **Uploaded CSV files** are saved to Vercel Blob Storage at `data/retraction_watch.csv`
- **Generated JSON files** are saved to blob storage at `dashboard_outputs/years/` and `dashboard_outputs/notice_years/`
- Files persist across deployments and function invocations
- On startup, the app loads files from blob storage to local filesystem for processing

## Environment Variables

Required environment variable:
- `BLOB_READ_WRITE_TOKEN`: Your Vercel Blob Storage read/write token

## Local Development

For local development without blob storage:
- The app will work normally using local filesystem
- Blob storage is only used when `BLOB_READ_WRITE_TOKEN` is set
- Install dependencies: `pip install -r requirements.txt`

