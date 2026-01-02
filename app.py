from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import json
from werkzeug.utils import secure_filename
import subprocess
import sys

# Vercel Blob Storage - try to import, fallback if not available
try:
    from vercel_blob import put, list_blobs, head, del_blob
    BLOB_AVAILABLE = True
except ImportError:
    BLOB_AVAILABLE = False
    print("Warning: vercel_blob not installed. Blob storage will be disabled.")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'dashboard_outputs')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'years'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'notice_years'), exist_ok=True)

# Vercel Blob Storage configuration
BLOB_READ_WRITE_TOKEN = os.environ.get('BLOB_READ_WRITE_TOKEN')
USE_BLOB_STORAGE = BLOB_AVAILABLE and BLOB_READ_WRITE_TOKEN is not None

def save_to_blob(filepath, blob_path):
    """Save file to Vercel Blob Storage"""
    if not USE_BLOB_STORAGE:
        return False
    try:
        with open(filepath, 'rb') as f:
            file_content = f.read()
        # Vercel Blob put API
        result = put(blob_path, file_content, token=BLOB_READ_WRITE_TOKEN, access='public')
        if result and hasattr(result, 'url'):
            print(f"File saved to blob: {result.url}")
            return True
        return False
    except Exception as e:
        print(f"Error saving to blob: {e}")
        return False

def load_from_blob(blob_path, local_path):
    """Load file from Vercel Blob Storage"""
    if not USE_BLOB_STORAGE:
        return False
    try:
        # Get blob info
        blob_info = head(blob_path, token=BLOB_READ_WRITE_TOKEN)
        if blob_info and hasattr(blob_info, 'url'):
            # Download the blob content
            import requests
            response = requests.get(blob_info.url, timeout=30)
            response.raise_for_status()
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"File loaded from blob: {blob_path}")
            return True
    except Exception as e:
        print(f"Error loading from blob: {e}")
    return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all available dashboard JSON files"""
    files = {
        'years': [],
        'notice_years': []
    }
    
    # Try to load files from blob storage first, then fallback to local
    if USE_BLOB_STORAGE:
        try:
            # Load CSV from blob if local file doesn't exist
            csv_blob_path = 'data/retraction_watch.csv'
            csv_local_path = os.path.join(DATA_DIR, 'retraction_watch.csv')
            if not os.path.exists(csv_local_path):
                load_from_blob(csv_blob_path, csv_local_path)
            
            # Load JSON files from blob storage
            # List and load JSON files from blob
            try:
                blob_list = list_blobs(token=BLOB_READ_WRITE_TOKEN, prefix='dashboard_outputs/')
                if blob_list and hasattr(blob_list, 'blobs'):
                    for blob in blob_list.blobs:
                        if blob.path.endswith('.json'):
                            # Extract folder and filename
                            parts = blob.path.split('/')
                            if len(parts) >= 3:
                                folder = parts[1]  # years or notice_years
                                filename = parts[2]
                                local_path = os.path.join(OUTPUT_DIR, folder, filename)
                                # Only load if local file doesn't exist or is older
                                if not os.path.exists(local_path) or (hasattr(blob, 'uploadedAt') and os.path.getmtime(local_path) < blob.uploadedAt):
                                    load_from_blob(blob.path, local_path)
            except Exception as e:
                print(f"Error loading JSON files from blob: {e}")
        except Exception as e:
            print(f"Error loading from blob: {e}")
    
    # List years folder
    years_dir = os.path.join(OUTPUT_DIR, 'years')
    if os.path.exists(years_dir):
        for filename in sorted(os.listdir(years_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(years_dir, filename)
                size = os.path.getsize(filepath)
                files['years'].append({
                    'name': filename,
                    'size': size,
                    'path': f'years/{filename}'
                })
    
    # List notice_years folder
    notice_dir = os.path.join(OUTPUT_DIR, 'notice_years')
    if os.path.exists(notice_dir):
        for filename in sorted(os.listdir(notice_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(notice_dir, filename)
                size = os.path.getsize(filepath)
                files['notice_years'].append({
                    'name': filename,
                    'size': size,
                    'path': f'notice_years/{filename}'
                })
    
    return jsonify(files)

@app.route('/api/view/<folder>/<filename>')
def view_file(folder, filename):
    """View a specific JSON file"""
    if folder not in ['years', 'notice_years']:
        return jsonify({'error': 'Invalid folder'}), 400
    
    filepath = os.path.join(OUTPUT_DIR, folder, filename)
    if not os.path.exists(filepath) or not filename.endswith('.json'):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return jsonify({
            'filename': filename,
            'folder': folder,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<folder>/<filename>')
def download_file(folder, filename):
    """Download a JSON file"""
    if folder not in ['years', 'notice_years']:
        return jsonify({'error': 'Invalid folder'}), 400
    
    directory = os.path.join(OUTPUT_DIR, folder)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process a CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400
    
    try:
        # Save uploaded file with fixed name (replace existing)
        filename = 'retraction_watch.csv'  # Fixed filename
        filepath = os.path.join(DATA_DIR, filename)
        file.save(filepath)  # Save locally first
        
        # Also save to Vercel Blob Storage if available
        if USE_BLOB_STORAGE:
            blob_path = f'data/{filename}'
            if save_to_blob(filepath, blob_path):
                print(f"File saved to Vercel Blob Storage: {blob_path}")
        
        # Determine which script to run based on file name
        if 'retraction' in filename.lower() or 'watch' in filename.lower():
            # Process with main script
            script_path = os.path.join(SCRIPTS_DIR, 'generate_dashboard_json.py')
            output_path = os.path.join(OUTPUT_DIR, 'years', 'dashboard_table.json')
            
            # Run the script
            result = subprocess.run(
                [sys.executable, script_path, filepath, output_path],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            
            if result.returncode != 0:
                return jsonify({
                    'error': 'Processing failed',
                    'details': result.stderr
                }), 500
            
            # Also generate filtered versions
            filter_script = os.path.join(SCRIPTS_DIR, 'generate_filtered_dashboards.py')
            filter_result = subprocess.run(
                [sys.executable, filter_script, filepath, OUTPUT_DIR],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            
            # Save generated JSON files to blob storage
            if USE_BLOB_STORAGE:
                try:
                    # Save all generated JSON files to blob
                    for folder in ['years', 'notice_years']:
                        folder_path = os.path.join(OUTPUT_DIR, folder)
                        if os.path.exists(folder_path):
                            for json_file in os.listdir(folder_path):
                                if json_file.endswith('.json'):
                                    json_path = os.path.join(folder_path, json_file)
                                    blob_json_path = f'dashboard_outputs/{folder}/{json_file}'
                                    if save_to_blob(json_path, blob_json_path):
                                        print(f"Saved {json_file} to blob storage")
                except Exception as e:
                    print(f"Error saving JSON files to blob: {e}")
            
            message = f'File processed successfully and saved as {filename}.'
            if USE_BLOB_STORAGE:
                message += ' File saved to Vercel Blob Storage and will persist.'
            else:
                message += ' File saved locally.'
            
            return jsonify({
                'success': True,
                'message': message,
                'filename': filename,
                'blob_storage': USE_BLOB_STORAGE,
                'output': result.stdout
            })
        else:
            return jsonify({
                'error': 'File name should contain "retraction" or "watch"'
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/process', methods=['POST'])
def process_file():
    """Process an existing CSV file"""
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Run the filtered dashboards script
        filter_script = os.path.join(SCRIPTS_DIR, 'generate_filtered_dashboards.py')
        result = subprocess.run(
            [sys.executable, filter_script, filepath, OUTPUT_DIR],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        if result.returncode != 0:
            return jsonify({
                'error': 'Processing failed',
                'details': result.stderr
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'output': result.stdout
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import socket
    
    # Find an available port
    def find_free_port(start_port=5000):
        port = start_port
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
                port += 1
    
    port = find_free_port(5000)
    if port != 5000:
        print(f"Port 5000 is in use, using port {port} instead")
    
    print(f"\n{'='*60}")
    print(f"Retraction Watch Dashboard Generator")
    print(f"Access the application at: http://localhost:{port}")
    print(f"{'='*60}\n")
    
    app.run(debug=True, host='0.0.0.0', port=port)

