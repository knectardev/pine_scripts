"""
Pine Script Library - Flask API Server
Provides CRUD operations for managing Pine Script metadata
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DATA_FILE = 'data/scripts.json'
BACKUP_DIR = 'data/backups'

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)


def load_scripts():
    """Load scripts from JSON file"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"scripts": []}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {DATA_FILE}")
        return {"scripts": []}


def save_scripts(data):
    """Save scripts to JSON file with backup"""
    # Create backup before saving
    if os.path.exists(DATA_FILE):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f'scripts_{timestamp}.json')
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            backup_data = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(backup_data)
        
        # Keep only last 10 backups
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('scripts_')])
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                os.remove(os.path.join(BACKUP_DIR, old_backup))
    
    # Save new data
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Serve static files
@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('web/'):
        return send_from_directory('.', path)
    elif path.startswith('data/'):
        return send_from_directory('.', path)
    return send_from_directory('web', path)


# API Routes

@app.route('/api/scripts', methods=['GET'])
def get_scripts():
    """Get all scripts"""
    data = load_scripts()
    return jsonify(data)


@app.route('/api/scripts/<script_id>', methods=['GET'])
def get_script(script_id):
    """Get a single script by ID"""
    data = load_scripts()
    script = next((s for s in data['scripts'] if s['id'] == script_id), None)
    
    if script:
        return jsonify(script)
    else:
        return jsonify({"error": "Script not found"}), 404


@app.route('/api/scripts', methods=['POST'])
def create_script():
    """Create a new script"""
    try:
        new_script = request.json
        
        # Validate required fields
        required_fields = ['name', 'type', 'version', 'filePath']
        for field in required_fields:
            if field not in new_script:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate ID if not provided
        if 'id' not in new_script or not new_script['id']:
            new_script['id'] = str(uuid.uuid4())[:8]
        
        # Add timestamps
        now = datetime.utcnow().isoformat() + 'Z'
        if 'dateCreated' not in new_script:
            new_script['dateCreated'] = now
        new_script['dateModified'] = now
        
        # Set defaults
        if 'pineVersion' not in new_script:
            new_script['pineVersion'] = 5
        if 'status' not in new_script:
            new_script['status'] = 'active'
        
        # Load existing data
        data = load_scripts()
        
        # Check for duplicate ID
        if any(s['id'] == new_script['id'] for s in data['scripts']):
            return jsonify({"error": "Script with this ID already exists"}), 409
        
        # Add new script
        data['scripts'].append(new_script)
        
        # Save
        save_scripts(data)
        
        return jsonify(new_script), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>', methods=['PUT'])
def update_script(script_id):
    """Update an existing script"""
    try:
        updated_data = request.json
        
        # Load existing data
        data = load_scripts()
        
        # Find script
        script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
        
        if script_index is None:
            return jsonify({"error": "Script not found"}), 404
        
        # Update timestamp
        updated_data['dateModified'] = datetime.utcnow().isoformat() + 'Z'
        
        # Preserve dateCreated if not provided
        if 'dateCreated' not in updated_data:
            updated_data['dateCreated'] = data['scripts'][script_index].get('dateCreated', updated_data['dateModified'])
        
        # Ensure ID remains the same
        updated_data['id'] = script_id
        
        # Update script
        data['scripts'][script_index] = updated_data
        
        # Save
        save_scripts(data)
        
        return jsonify(updated_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>', methods=['DELETE'])
def delete_script(script_id):
    """Delete a script"""
    try:
        # Load existing data
        data = load_scripts()
        
        # Find script
        script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
        
        if script_index is None:
            return jsonify({"error": "Script not found"}), 404
        
        # Remove script
        deleted_script = data['scripts'].pop(script_index)
        
        # Save
        save_scripts(data)
        
        return jsonify({"message": "Script deleted successfully", "script": deleted_script})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/backups', methods=['GET'])
def list_backups():
    """List all available backups"""
    try:
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('scripts_')], reverse=True)
        return jsonify({"backups": backups})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/backups/<filename>', methods=['POST'])
def restore_backup(filename):
    """Restore from a backup file"""
    try:
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({"error": "Backup file not found"}), 404
        
        # Read backup
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Save current as backup before restoring
        save_scripts(backup_data)
        
        return jsonify({"message": "Backup restored successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Pine Script Library API Server")
    print("=" * 60)
    print("📍 Server running at: http://localhost:5000")
    print("🌐 Open web interface: http://localhost:5000")
    print("📊 API Endpoints:")
    print("   GET    /api/scripts          - List all scripts")
    print("   GET    /api/scripts/:id      - Get single script")
    print("   POST   /api/scripts          - Create new script")
    print("   PUT    /api/scripts/:id      - Update script")
    print("   DELETE /api/scripts/:id      - Delete script")
    print("   GET    /api/backups          - List backups")
    print("   POST   /api/backups/:file    - Restore backup")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
