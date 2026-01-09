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
import re
import shutil
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DATA_FILE = 'data/scripts.json'
BACKUP_DIR = 'data/backups'

# LLM Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'openai')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')

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


def save_scripts(data, create_backup=True):
    """Save scripts to JSON file with optional backup"""
    # Create backup before saving (only if requested and file exists)
    if create_backup and os.path.exists(DATA_FILE):
        # Check if enough time has passed since last backup (avoid backup spam)
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('scripts_')])
        should_backup = True
        
        if backups:
            # Get timestamp of most recent backup
            last_backup = backups[-1]
            last_backup_time = datetime.strptime(last_backup.replace('scripts_', '').replace('.json', ''), '%Y%m%d_%H%M%S')
            time_since_backup = (datetime.now() - last_backup_time).total_seconds()
            
            # Only create backup if more than 5 minutes have passed
            should_backup = time_since_backup > 300  # 5 minutes
        
        if should_backup:
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


# ============================================================================
# VERSION CONTROL FUNCTIONS
# ============================================================================

def get_script_base_dir(file_path):
    """Get base directory for script versions - uses archive/ subdirectory
    
    IMPORTANT: This function normalizes ANY path back to the correct project archive folder.
    It handles:
    - Clean paths: scripts/indicators/my-indicator/my-indicator.pine
    - Already archived: scripts/indicators/my-indicator/archive/my-indicator_v1.0.0.pine
    - Deeply nested (BUG): scripts/indicators/my-indicator/archive/v1.0/archive/v1.1/v1.2.pine
    
    All return: scripts/indicators/my-indicator/archive
    """
    path = Path(file_path)
    parts = list(path.parts)
    
    # Extract project name from filename or path
    project_name = get_project_name_from_path(file_path)
    
    # Find the project root by looking for the project name in the path
    # OR finding the first 'archive' folder and going one level up
    project_root_idx = None
    
    # Strategy 1: If 'archive' exists in path, project root is the folder before first 'archive'
    if 'archive' in parts:
        first_archive_idx = parts.index('archive')
        if first_archive_idx > 0:
            project_root_idx = first_archive_idx - 1
    
    # Strategy 2: Find folder matching project name
    if project_root_idx is None:
        for i, part in enumerate(parts):
            if part == project_name:
                project_root_idx = i
                break
    
    # Strategy 3: If file is in flat structure (e.g., scripts/strategies/my-strategy.pine)
    if project_root_idx is None:
        # Parent directory is the category (strategies, indicators, etc.)
        # We need to create project folder
        project_root = path.parent / project_name
    else:
        # Reconstruct path up to project root
        project_root = Path(*parts[:project_root_idx + 1])
    
    # Return the archive subdirectory
    archive_dir = project_root / 'archive'
    return archive_dir


def get_project_name_from_path(file_path):
    """Extract the project name from a file path for version naming"""
    # e.g., scripts/strategies/my-strategy/my-strategy.pine -> "my-strategy"
    # or scripts/strategies/my-strategy/archive/my-strategy_v1.0.0.pine -> "my-strategy"
    path = Path(file_path)
    
    # If in archive folder, parent.parent is project folder
    if 'archive' in path.parts:
        # Find the project folder (before 'archive')
        parts = list(path.parts)
        archive_idx = parts.index('archive')
        if archive_idx > 0:
            return parts[archive_idx - 1]
    
    # If filename matches pattern: name.pine or name_vX.X.X.pine
    stem = path.stem
    if '_v' in stem:
        # Remove version suffix: "my-strategy_v1.0.0" -> "my-strategy"
        return stem.split('_v')[0]
    
    # Check if parent folder name matches stem (project structure)
    if path.parent.name == stem:
        return stem
    
    # Otherwise use the stem directly
    return stem


def ensure_version_directory(script):
    """Ensure version directory exists and migrate if needed"""
    file_path = script.get('filePath')
    if not file_path:
        return None
    
    version_dir = get_script_base_dir(file_path)
    version_dir.mkdir(parents=True, exist_ok=True)
    
    return version_dir


def migrate_script_to_versioning(script):
    """
    Migrate an existing script to version control system
    Creates v1.0.0 from current file
    """
    file_path = script.get('filePath')
    if not file_path or not os.path.exists(file_path):
        return False
    
    # Check if already migrated
    if 'versions' in script and len(script.get('versions', [])) > 0:
        return True  # Already versioned
    
    # Read current file
    with open(file_path, 'r', encoding='utf-8') as f:
        current_code = f.read()
    
    # Create version directory
    version_dir = ensure_version_directory(script)
    if not version_dir:
        return False
    
    # Determine initial version
    initial_version = script.get('version', script.get('currentVersion', '1.0.0'))
    
    # Create versioned file with proper naming: project-name_vX.X.X.pine
    project_name = get_project_name_from_path(file_path)
    version_file = version_dir / f"{project_name}_v{initial_version}.pine"
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(current_code)
    
    # Initialize versions array
    script['versions'] = [{
        'version': initial_version,
        'filePath': str(version_file),
        'dateCreated': script.get('dateModified', script.get('dateCreated', datetime.utcnow().isoformat() + 'Z')),
        'changelog': 'Initial version (auto-migrated)',
        'author': script.get('author', 'system'),
        'isActive': True
    }]
    
    script['currentVersion'] = initial_version
    script['version'] = initial_version  # Keep top-level version in sync
    
    # Keep old filePath for backward compatibility, but point to version
    script['filePath'] = str(version_file)
    
    return True


def create_new_version(script, new_version, code, changelog, author='user'):
    """
    Create a new version of a script
    Returns: (success, new_version_info, error_message)
    """
    try:
        # Ensure versioning is set up
        if 'versions' not in script or len(script.get('versions', [])) == 0:
            migrate_script_to_versioning(script)
        
        # Create version directory
        version_dir = ensure_version_directory(script)
        if not version_dir:
            return False, None, "Could not create version directory"
        
        # Get metadata for header injection
        project_name = get_project_name_from_path(script.get('filePath'))
        version_file = version_dir / f"{project_name}_v{new_version}.pine"
        
        # Update/inject version metadata in code header
        code = update_version_in_code(
            code, 
            new_version, 
            script_name=script.get('name', 'Unknown Script'),
            script_type=script.get('type', 'indicator').upper(),
            filename=f"{project_name}_v{new_version}.pine",
            changelog=changelog,
            author=script.get('author', 'Your Name')
        )
        
        # Create new version file with proper naming: project-name_vX.X.X.pine
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Deactivate all versions
        for v in script.get('versions', []):
            v['isActive'] = False
        
        # Create new version entry
        new_version_info = {
            'version': new_version,
            'filePath': str(version_file),
            'dateCreated': datetime.utcnow().isoformat() + 'Z',
            'changelog': changelog,
            'author': author,
            'isActive': True
        }
        
        # Add to versions array
        if 'versions' not in script:
            script['versions'] = []
        script['versions'].append(new_version_info)
        
        # Update current version
        script['currentVersion'] = new_version
        script['version'] = new_version  # Keep top-level version in sync
        script['filePath'] = str(version_file)
        script['dateModified'] = new_version_info['dateCreated']
        
        return True, new_version_info, None
        
    except Exception as e:
        return False, None, str(e)


def get_version_code(script, version):
    """Get code for a specific version"""
    versions = script.get('versions', [])
    version_info = next((v for v in versions if v['version'] == version), None)
    
    if not version_info:
        return None, "Version not found"
    
    file_path = version_info.get('filePath')
    if not file_path or not os.path.exists(file_path):
        return None, "Version file not found"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        return code, None
    except Exception as e:
        return None, str(e)


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
    """Create a new script with initial file and version control"""
    try:
        new_script = request.json
        
        # Validate required fields
        required_fields = ['name', 'type', 'filePath']
        for field in required_fields:
            if field not in new_script:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate ID if not provided
        if 'id' not in new_script or not new_script['id']:
            new_script['id'] = str(uuid.uuid4())[:8]
        
        # Set version if not provided
        if 'version' not in new_script:
            new_script['version'] = '1.0.0'
        
        initial_version = new_script['version']
        
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
        
        # Create initial Pine Script file content
        script_type = new_script['type']
        script_name = new_script['name']
        author = new_script.get('author', 'user')
        description = new_script.get('description', '')
        
        initial_code = generate_initial_script_code(
            script_name, 
            script_type, 
            initial_version, 
            author, 
            description
        )
        
        # Set up version control structure
        file_path = new_script['filePath']
        version_dir = get_script_base_dir(file_path)
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial version file with proper naming: project-name_vX.X.X.pine
        project_name = get_project_name_from_path(file_path)
        version_file = version_dir / f"{project_name}_v{initial_version}.pine"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(initial_code)
        
        # Initialize version control
        new_script['currentVersion'] = initial_version
        new_script['version'] = initial_version  # Keep top-level version in sync
        new_script['filePath'] = str(version_file)
        new_script['versions'] = [{
            'version': initial_version,
            'filePath': str(version_file),
            'dateCreated': now,
            'changelog': 'Initial version',
            'author': author,
            'isActive': True
        }]
        
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


def generate_initial_script_code(name, script_type, version, author, description):
    """Generate initial Pine Script code template"""
    
    # Determine declaration based on type
    if script_type == 'strategy':
        declaration = f'strategy("{name}", overlay=true)'
    else:  # indicator or study
        declaration = f'indicator("{name}", overlay=true)'
    
    template = f"""// This Pine Script was created via Pine Script Library
// © {author}
//@version=5
{declaration}

// ————— Constants
// Add your constants here

// ————— Inputs
// Add your input parameters here

// ————— Calculations
// Add your calculations here

// ————— Visuals
// Add your plots and visual elements here
"""
    
    if description:
        # Add description as comment at the top
        desc_lines = description.split('\n')
        desc_comment = '\n'.join([f'// {line}' for line in desc_lines])
        template = f"""// {name}
{desc_comment}
""" + template
    
    return template


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
        
        existing_script = data['scripts'][script_index]
        
        # Update timestamp
        updated_data['dateModified'] = datetime.utcnow().isoformat() + 'Z'
        
        # Preserve dateCreated if not provided
        if 'dateCreated' not in updated_data:
            updated_data['dateCreated'] = existing_script.get('dateCreated', updated_data['dateModified'])
        
        # Ensure ID remains the same
        updated_data['id'] = script_id
        
        # CRITICAL: Preserve file path and version structure (files on disk don't move when name changes)
        if 'filePath' in existing_script:
            updated_data['filePath'] = existing_script['filePath']
        if 'versions' in existing_script:
            updated_data['versions'] = existing_script['versions']
        if 'currentVersion' in existing_script:
            updated_data['currentVersion'] = existing_script['currentVersion']
        
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


@app.route('/api/scripts/<script_id>/code', methods=['GET'])
def get_script_code(script_id):
    """Get Pine Script source code for a script (current version or specific version)"""
    try:
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Check if specific version requested
        version = request.args.get('version')
        
        if version:
            # Get specific version
            code, error = get_version_code(script, version)
            if error:
                return jsonify({"error": error}), 404
            
            versions = script.get('versions', [])
            version_info = next((v for v in versions if v['version'] == version), None)
            
            return jsonify({
                "id": script_id,
                "name": script.get('name'),
                "version": version,
                "filePath": version_info.get('filePath') if version_info else None,
                "code": code,
                "versionInfo": version_info
            })
        else:
            # Get current version - PRIORITIZE versioned file if it exists
            current_version = script.get('currentVersion')
            
            if current_version and 'versions' in script and len(script.get('versions', [])) > 0:
                # Use the versioned file (from version system)
                code, error = get_version_code(script, current_version)
                if not error:
                    versions = script.get('versions', [])
                    version_info = next((v for v in versions if v['version'] == current_version), None)
                    return jsonify({
                        "id": script_id,
                        "name": script.get('name'),
                        "version": current_version,
                        "filePath": version_info.get('filePath') if version_info else None,
                        "code": code,
                        "versionInfo": version_info
                    })
                else:
                    # Fall back to main file if versioned file not found
                    file_path = script.get('filePath')
                    if not file_path or not os.path.exists(file_path):
                        return jsonify({"error": "Script file not found"}), 404
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    return jsonify({
                        "id": script_id,
                        "name": script.get('name'),
                        "version": current_version,
                        "filePath": file_path,
                        "code": code
                    })
            else:
                # No version system yet - use main file
                file_path = script.get('filePath')
                if not file_path:
                    return jsonify({"error": "No file path specified for this script"}), 400
                
                # Read the Pine Script file
                if not os.path.exists(file_path):
                    return jsonify({"error": f"Script file not found at: {file_path}"}), 404
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                return jsonify({
                    "id": script_id,
                    "name": script.get('name'),
                    "version": script.get('currentVersion'),
                    "filePath": file_path,
                    "code": code
                })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>/versions', methods=['GET'])
def get_script_versions(script_id):
    """Get version history for a script"""
    try:
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Auto-migrate if needed
        if 'versions' not in script or len(script.get('versions', [])) == 0:
            migrate_script_to_versioning(script)
            # Save migration
            script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
            if script_index is not None:
                data['scripts'][script_index] = script
                save_scripts(data)
        
        versions = script.get('versions', [])
        
        # Sort by date (newest first)
        sorted_versions = sorted(versions, key=lambda v: v.get('dateCreated', ''), reverse=True)
        
        return jsonify({
            'scriptId': script_id,
            'currentVersion': script.get('currentVersion'),
            'versions': sorted_versions,
            'totalVersions': len(sorted_versions)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>/versions/<version>/restore', methods=['POST'])
def restore_version(script_id, version):
    """
    Restore a previous version
    Options:
    - mode: 'activate' (make this version current) or 'new' (create new version based on this)
    """
    try:
        request_data = request.json or {}
        mode = request_data.get('mode', 'activate')  # Default: activate
        
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Get the version code
        code, error = get_version_code(script, version)
        if error:
            return jsonify({"error": error}), 404
        
        if mode == 'activate':
            # Set this version as active
            versions = script.get('versions', [])
            
            # Deactivate all
            for v in versions:
                v['isActive'] = False
            
            # Activate requested version
            version_info = next((v for v in versions if v['version'] == version), None)
            if version_info:
                version_info['isActive'] = True
                script['currentVersion'] = version
                script['version'] = version  # Keep top-level version in sync
                script['filePath'] = version_info['filePath']
                script['dateModified'] = datetime.utcnow().isoformat() + 'Z'
            
            result = {
                'success': True,
                'mode': 'activate',
                'activeVersion': version,
                'message': f'Version {version} is now active'
            }
            
        elif mode == 'new':
            # Create new version based on this one
            current_version = script.get('currentVersion', '1.0.0')
            new_version = increment_version(current_version)
            
            changelog = f'Created from version {version}'
            
            success, version_info, error = create_new_version(
                script,
                new_version,
                code,
                changelog,
                author=request_data.get('author', 'user')
            )
            
            if not success:
                return jsonify({"error": error or "Failed to create new version"}), 500
            
            result = {
                'success': True,
                'mode': 'new',
                'newVersion': new_version,
                'basedOn': version,
                'message': f'Created new version {new_version} based on {version}',
                'versionInfo': version_info
            }
        else:
            return jsonify({"error": "Invalid mode. Use 'activate' or 'new'"}), 400
        
        # Save changes
        script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
        if script_index is not None:
            data['scripts'][script_index] = script
            save_scripts(data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>/review', methods=['GET'])
def review_script_code(script_id):
    """Review Pine Script code against standards and best practices (current or specific version)"""
    try:
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Check if specific version requested
        version = request.args.get('version')
        
        if version:
            # Get specific version code
            code, error = get_version_code(script, version)
            if error:
                return jsonify({"error": error}), 404
            script_name = f"{script.get('name', 'Unknown')} (v{version})"
        else:
            # Get current version - PRIORITIZE versioned file if it exists
            current_version = script.get('currentVersion')
            
            if current_version and 'versions' in script and len(script.get('versions', [])) > 0:
                # Use the versioned file (from version system)
                code, error = get_version_code(script, current_version)
                if not error:
                    script_name = f"{script.get('name', 'Unknown')} (v{current_version})"
                else:
                    # Fall back to main file if versioned file not found
                    file_path = script.get('filePath')
                    if not file_path or not os.path.exists(file_path):
                        return jsonify({"error": "Script file not found"}), 404
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    script_name = f"{script.get('name', 'Unknown')} (main file)"
            else:
                # No version system yet - use main file
                file_path = script.get('filePath')
                if not file_path:
                    return jsonify({"error": "No file path specified for this script"}), 400
                
                # Read the Pine Script file
                if not os.path.exists(file_path):
                    return jsonify({"error": f"Script file not found at: {file_path}"}), 404
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                script_name = f"{script.get('name', 'Unknown')} (main file)"
        
        # Perform code review
        review_results = perform_code_review(code, script_name)
        
        # Add version info to results
        review_results['reviewedVersion'] = version if version else script.get('currentVersion')
        
        return jsonify(review_results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def perform_code_review(code, script_name):
    """
    Comprehensive code review based on:
    - PINE_SCRIPT_STANDARDS.md
    - LOGICAL_SANITY_CHECKS.md
    - SANITY_CHECKS_QUICK_REF.md
    """
    issues = []
    recommendations = []
    lines = code.split('\n')
    
    # ============================================================================
    # 1. VERSION CHECK (CRITICAL)
    # ============================================================================
    # Check for version 5 or 6 (both are acceptable)
    has_version_5 = '//@version=5' in code
    has_version_6 = '//@version=6' in code
    
    if not has_version_5 and not has_version_6:
        issues.append({
            'category': 'Script Structure',
            'check': 'Pine Script Version',
            'severity': 'CRITICAL',
            'message': 'Script must use //@version=5 or //@version=6 declaration',
            'line': 1
        })
    elif has_version_5:
        issues.append({
            'category': 'Script Structure',
            'check': 'Pine Script Version',
            'severity': 'PASS',
            'message': 'Using Pine Script v5 ✓'
        })
    else:  # has_version_6
        issues.append({
            'category': 'Script Structure',
            'check': 'Pine Script Version',
            'severity': 'PASS',
            'message': 'Using Pine Script v6 ✓'
        })
    
    # ============================================================================
    # 2. NAMING CONVENTIONS CHECK
    # ============================================================================
    
    # Track multi-line comment blocks
    in_multiline_comment = False
    
    # Check for snake_case variables (should be camelCase)
    # Pattern: snake_case followed by = (but not ==, !=, <=, >=)
    # This should match variable assignments like: my_var = value
    snake_case_pattern = re.compile(r'\b([a-z]+_[a-z_]+)\s*=(?!=|<|>)')
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if '=' in line and not stripped.startswith('//') and not in_multiline_comment:
            matches = snake_case_pattern.findall(line)
            for match in matches:
                # Skip if it's a constant (all caps)
                if match.isupper():
                    continue
                
                # Skip function parameters (they appear after opening paren or comma within parens)
                # Check if this is inside a function call by looking for context
                # Pattern: word_name = appears after ( or , and before ) - this is a function parameter
                if re.search(r'[(,]\s*[^)]*\b' + re.escape(match) + r'\s*=', line):
                    continue  # This is a function parameter like strategy(..., initial_capital=50000)
                
                # This is a real variable assignment
                issues.append({
                    'category': 'Naming Conventions',
                    'check': 'camelCase Variables',
                    'severity': 'HIGH',
                    'message': f'Variable "{match}" uses snake_case. Should use camelCase (e.g., "{to_camel_case(match)}")',
                    'line': i,
                    'code': line.strip()
                })
    
    # Reset comment tracking
    in_multiline_comment = False
    
    # Check for constants without SNAKE_CASE
    const_pattern = re.compile(r'(?:const|^)\s+(?:int|float|bool|string|color)\s+([a-z][a-zA-Z0-9]*)\s*=')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if ('const' in line or (stripped and not stripped.startswith('//'))) and not in_multiline_comment:
            matches = const_pattern.findall(line)
            for match in matches:
                if match.islower() and 'input' not in match.lower():
                    issues.append({
                        'category': 'Naming Conventions',
                        'check': 'SNAKE_CASE Constants',
                        'severity': 'HIGH',
                        'message': f'Constant "{match}" should use SNAKE_CASE (e.g., "{match.upper()}")',
                        'line': i,
                        'code': line.strip()
                    })
    
    # Reset comment tracking
    in_multiline_comment = False
    
    # Check for input variables without Input suffix
    input_pattern = re.compile(r'(\w+)\s*=\s*input\.(bool|int|float|string|color|time|timeframe|source|session)')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if not stripped.startswith('//') and not in_multiline_comment:
            matches = input_pattern.findall(line)
            for var_name, input_type in matches:
                # Check if variable name ends with Input suffix
                if not var_name.endswith('Input'):
                    suggested_name = var_name + 'Input'
                    issues.append({
                        'category': 'Naming Conventions',
                        'check': 'Input Suffix',
                        'severity': 'HIGH',
                        'message': f'Input variable "{var_name}" should have "Input" suffix (e.g., "{suggested_name}")',
                        'line': i,
                        'code': line.strip(),
                        'quickfix': {
                            'type': 'rename_input_variable',
                            'old_name': var_name,
                            'new_name': suggested_name
                        }
                    })
    
    # ============================================================================
    # 3. FORMATTING CHECKS
    # ============================================================================
    
    # Track multi-line comment blocks to skip them
    in_multiline_comment = False
    
    # Check for operators without spaces
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue  # Skip the closing line too
        
        # Skip single-line comments and multi-line comment blocks
        if not stripped.startswith('//') and not in_multiline_comment:
            # Remove string literals to avoid false positives
            # This prevents matching operators inside strings like "2025-10-01" or "America/New_York"
            line_without_strings = re.sub(r'"[^"]*"', '""', line)
            line_without_strings = re.sub(r"'[^']*'", "''", line_without_strings)
            
            # Check for missing spaces around operators (but not in strings)
            # Pattern: alphanumeric directly touching operator directly touching alphanumeric
            if re.search(r'[a-zA-Z0-9_][+\-*/=<>!]+[a-zA-Z0-9_]', line_without_strings):
                # Exclude valid cases
                if '://' not in line_without_strings and '==' not in line_without_strings and '>=' not in line_without_strings and '<=' not in line_without_strings and '!=' not in line_without_strings:
                    # Additional check: skip lines with function parameters (those should not have spaces)
                    # Function parameters come after ( or ,
                    # Example: input.float(0.20, step=0.05) is correct
                    if not re.search(r'[,(]\s*\w+=[^=]', line_without_strings):
                        issues.append({
                            'category': 'Formatting',
                            'check': 'Operator Spacing',
                            'severity': 'WARNING',
                            'message': 'Missing spaces around operators. Use spaces for readability (e.g., "a = b + c")',
                            'line': i,
                            'code': line.strip()[:60]
                        })
    
    # ============================================================================
    # 4. PINE SCRIPT SYNTAX CHECKS
    # ============================================================================
    
    # Reset comment tracking
    in_multiline_comment = False
    
    # Check for ternary operators split across lines without proper indentation
    # When a line ends with ?, the next line MUST be indented (at least 1 space)
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if stripped.startswith('//') or in_multiline_comment:
            continue
        
        # Check if line ends with an operator that requires continuation indentation
        # Pine Script requires indentation for line continuation with ANY operator
        continuation_operators = [
            '?',      # Ternary operator
            'and',    # Logical AND
            'or',     # Logical OR
            '+',      # Addition
            '-',      # Subtraction (but not negative numbers)
            '*',      # Multiplication
            '/',      # Division
            '==',     # Equality
            '!=',     # Not equal
            '>',      # Greater than
            '<',      # Less than
            '>=',     # Greater or equal
            '<=',     # Less or equal
        ]
        
        # Special case: lines ending with : that are part of ternary
        is_continuation_line = False
        
        # Check for operators at end of line
        for op in continuation_operators:
            if stripped.endswith(op):
                is_continuation_line = True
                break
        
        # Special case: line has ? and ends with :
        if not is_continuation_line and stripped.endswith(':') and '?' in stripped:
            is_continuation_line = True
        
        if is_continuation_line:
            # Find the next non-empty, non-comment line
            next_idx = i + 1
            while next_idx < len(lines):
                next_line = lines[next_idx]
                next_stripped = next_line.strip()
                
                # Skip empty lines and comments
                if not next_stripped or next_stripped.startswith('//'):
                    next_idx += 1
                    continue
                
                # Found the continuation line - check indentation
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # Pine Script requires continuation line to be indented
                # (at least 1 space more than the line with operator)
                if next_indent <= current_indent:
                    # Determine which operator the line ends with
                    ending_operator = '?'
                    for op in continuation_operators:
                        if stripped.endswith(op):
                            ending_operator = op
                            break
                    if stripped.endswith(':') and '?' in stripped:
                        ending_operator = ':'
                    
                    issues.append({
                        'category': 'Syntax',
                        'check': 'Operator Line Continuation',
                        'severity': 'CRITICAL',
                        'message': f'Line continuation requires indentation. Line {i+1} ends with "{ending_operator}" but line {next_idx+1} is not indented. Add at least 1 space (preferably 4) to indent the continuation line.',
                        'line': i + 1,
                        'code': stripped[:80],
                        'quickfix': {
                            'type': 'indent_operator_continuation',
                            'operator_line': i,
                            'continuation_line': next_idx,
                            'current_indent': next_indent,
                            'required_indent': current_indent + 4  # Use 4 spaces (standard Pine Script)
                        }
                    })
                break
    
    # Reset comment tracking
    in_multiline_comment = False
    
    # Check for multi-line if statements without proper indentation or body
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if stripped.startswith('//') or in_multiline_comment:
            continue
        
        # Check for if statements without a body on the same line
        if re.match(r'^(\s*)(if|else\s+if)\s+.+$', line) and not '=>' in line:
            # This is a multi-line if statement
            # Check if next line is properly indented
            if i < len(lines):
                next_line = lines[i] if i < len(lines) else ""
                next_stripped = next_line.strip()
                
                # Skip empty lines and comments
                next_idx = i
                while next_idx < len(lines) and (not next_stripped or next_stripped.startswith('//')):
                    next_idx += 1
                    if next_idx < len(lines):
                        next_line = lines[next_idx]
                        next_stripped = next_line.strip()
                    else:
                        break
                
                # Check if next non-empty, non-comment line exists and is properly indented
                if next_stripped and next_idx < len(lines):
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # Pine Script requires EXACTLY 4 spaces of indentation (or multiples for nested blocks)
                    # The body must be indented 4 more spaces than the if statement
                    expected_indent = current_indent + 4
                    
                    # Check if it's not a new control statement at same or less indent
                    is_new_statement = re.match(r'^(if|else|var|const|for|while|float|int|bool|string)\s+', next_stripped)
                    
                    # If next line is not indented by exactly 4 spaces (or is a new statement), it's an error
                    if not is_new_statement and next_indent != expected_indent:
                        if next_indent <= current_indent:
                            # No indentation at all
                            message = f'Multi-line if statement body must be indented with 4 spaces. Line "{next_stripped[:40]}" has no indentation'
                        elif next_indent < expected_indent:
                            # Some indentation but not enough
                            spaces_short = expected_indent - next_indent
                            message = f'Multi-line if statement body needs {expected_indent} spaces total (currently has {next_indent}). Add {spaces_short} more space(s)'
                        else:
                            # Too much indentation (not a multiple of 4)
                            message = f'Multi-line if statement body has incorrect indentation ({next_indent} spaces). Should be {expected_indent} spaces'
                        
                        issues.append({
                            'category': 'Syntax',
                            'check': 'Multi-line If Statement',
                            'severity': 'CRITICAL',
                            'message': message,
                            'line': i,
                            'code': line.strip(),
                            'quickfix': {
                                'type': 'indent_if_body',
                                'if_line': i,
                                'body_start_line': next_idx + 1,
                                'expected_indent': expected_indent,
                                'current_indent': next_indent
                            }
                        })
    
    # ============================================================================
    # 5. TYPE MISMATCH CHECKS
    # ============================================================================
    
    # Common type mismatches where declared type doesn't match function return type
    type_mismatch_patterns = {
        # ta.change() returns int, not bool
        r'(const\s+)?bool\s+(\w+)\s*=\s*ta\.change\(': {
            'declared_type': 'bool',
            'actual_type': 'int',
            'function': 'ta.change()',
            'fix_type': 'change_type_to_int',
            'message': 'ta.change() returns "series int", not "bool". Either declare as "int" or add "!= 0" for boolean comparison'
        },
        # na() returns bool, but assigned to int/float
        r'(const\s+)?(int|float)\s+(\w+)\s*=\s*na\(': {
            'declared_type': 'int/float',
            'actual_type': 'bool',
            'function': 'na()',
            'fix_type': 'change_type_to_bool',
            'message': 'na() returns "bool", not "int" or "float". Declare as "bool"'
        },
        # ta.crossover/crossunder return bool, not int/float
        r'(const\s+)?(int|float)\s+(\w+)\s*=\s*ta\.cross(?:over|under)\(': {
            'declared_type': 'int/float',
            'actual_type': 'bool',
            'function': 'ta.crossover()/ta.crossunder()',
            'fix_type': 'change_type_to_bool',
            'message': 'ta.crossover()/ta.crossunder() returns "bool", not "int" or "float". Declare as "bool"'
        },
        # ta.pivothigh/pivotlow return float, not bool
        r'(const\s+)?bool\s+(\w+)\s*=\s*ta\.pivot(?:high|low)\(': {
            'declared_type': 'bool',
            'actual_type': 'float',
            'function': 'ta.pivothigh()/ta.pivotlow()',
            'fix_type': 'change_type_to_float',
            'message': 'ta.pivothigh()/ta.pivotlow() returns "series float", not "bool". Declare as "float"'
        },
        # ta.barssince returns int, not bool
        r'(const\s+)?bool\s+(\w+)\s*=\s*ta\.barssince\(': {
            'declared_type': 'bool',
            'actual_type': 'int',
            'function': 'ta.barssince()',
            'fix_type': 'change_type_to_int',
            'message': 'ta.barssince() returns "series int", not "bool". Declare as "int"'
        },
    }
    
    # Reset comment tracking
    in_multiline_comment = False
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if stripped.startswith('//') or in_multiline_comment:
            continue
        
        # Check for type mismatches
        for pattern, mismatch_info in type_mismatch_patterns.items():
            match = re.search(pattern, line)
            if match:
                issues.append({
                    'category': 'Type Mismatch',
                    'check': 'Variable Type Declaration',
                    'severity': 'CRITICAL',
                    'message': mismatch_info['message'],
                    'line': i,
                    'code': line.strip(),
                    'quickfix': {
                        'type': mismatch_info['fix_type'],
                        'function': mismatch_info['function']
                    }
                })
    
    # ============================================================================
    # 5B. INT/FLOAT IN BOOLEAN CONTEXT
    # ============================================================================
    
    # Track int/float variable declarations
    int_float_vars = {}  # Maps variable name -> (type, line)
    
    # First pass: collect int/float variable declarations
    in_multiline_comment = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if stripped.startswith('//') or in_multiline_comment:
            continue
        
        # Match variable declarations: int varName = ... or float varName = ...
        int_float_pattern = re.compile(r'\b(int|float)\s+(\w+)\s*=')
        match = int_float_pattern.search(line)
        if match:
            var_type = match.group(1)
            var_name = match.group(2)
            int_float_vars[var_name] = (var_type, i)
    
    # Second pass: check for int/float vars used in boolean contexts
    in_multiline_comment = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments
        if stripped.startswith('//') or in_multiline_comment:
            continue
        
        # Check for int/float variables used in boolean contexts
        # Pattern 1: if varName (should be: if varName != 0)
        # Pattern 2: if ... or varName (should be: if ... or varName != 0)
        # Pattern 3: if ... and varName (should be: if ... and varName != 0)
        
        if re.match(r'^\s*(if|while)\s+', line):
            # This is an if/while statement
            # Extract the condition part (everything after if/while until newline or comment)
            condition_match = re.match(r'^\s*(?:if|while)\s+(.+?)(?://|$)', line)
            if condition_match:
                condition = condition_match.group(1).strip()
                
                # Check each int/float var to see if it's used directly in condition
                for var_name, (var_type, decl_line) in int_float_vars.items():
                    # Pattern: varName followed by word boundary (not followed by comparison operator)
                    # Positive cases: "if varName", "if x or varName", "if varName and y"
                    # Negative cases (OK): "if varName != 0", "if varName > 5"
                    
                    # Check if variable appears in condition
                    if re.search(r'\b' + re.escape(var_name) + r'\b', condition):
                        # Check if it's followed by a comparison operator (OK)
                        # Pattern: varName NOT followed by !=, ==, >, <, >=, <=
                        if not re.search(r'\b' + re.escape(var_name) + r'\s*(?:!=|==|>=|<=|>|<)', condition):
                            # It's being used directly in boolean context
                            issues.append({
                                'category': 'Type Mismatch',
                                'check': 'Int/Float in Boolean Context',
                                'severity': 'CRITICAL',
                                'message': f'Variable "{var_name}" ({var_type}) used in boolean context. Add explicit comparison (e.g., "{var_name} != 0" or "{var_name} > 0")',
                                'line': i,
                                'code': stripped[:80],
                                'quickfix': {
                                    'type': 'add_explicit_comparison',
                                    'variable': var_name,
                                    'suggestion': f'{var_name} != 0'
                                }
                            })
                            break  # Only report once per line
    
    # ============================================================================
    # 6. PERFORMANCE CHECKS (ta.* function scoping)
    # ============================================================================
    
    # Reset and track multi-line comment blocks
    in_multiline_comment = False
    
    # Check for ta.* functions inside if blocks
    # NOTE: This check is for ta.* calls in the BODY of if/for/while blocks
    # Global-scope variable declarations with ta.* are OK
    ta_func_pattern = re.compile(r'ta\.\w+\(')
    if_block_stack = []  # Stack of (indent_level, line_number, expected_body_indent)
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            continue
        
        # Skip comments and empty lines
        if stripped.startswith('//') or in_multiline_comment or not stripped:
            continue
        
        current_indent = len(line) - len(line.lstrip())
        
        # Pop from stack when we're back at or below the if statement's indent level
        # This means we've exited the if block body
        while if_block_stack and current_indent <= if_block_stack[-1][0]:
            if_block_stack.pop()
        
        # Track if/for/while blocks
        if re.match(r'^(if|for|while)\s+', stripped):
            # Push this control statement's indent and expected body indent
            expected_body_indent = current_indent + 4
            if_block_stack.append((current_indent, i, expected_body_indent))
            continue  # Don't check the if line itself
        
        # Check for ta.* ONLY if we're currently inside an if block body
        # AND the current line is indented more than the if statement
        if len(if_block_stack) > 0:
            if_indent, if_line, expected_body_indent = if_block_stack[-1]
            
            # Only flag if this line is indented MORE than the if statement
            # (i.e., it's in the body of the if block)
            if current_indent > if_indent and ta_func_pattern.search(stripped):
                issues.append({
                    'category': 'Performance',
                    'check': 'ta.* Function Scoping (B8)',
                    'severity': 'CRITICAL',
                    'message': f'ta.* functions must be called unconditionally at global scope, not inside if/for/while blocks (control block starts at line {if_line}). This breaks internal state.',
                    'line': i,
                    'code': line.strip()[:80]
                })
    
    # ============================================================================
    # 5. LOGICAL SANITY CHECKS
    # ============================================================================
    
    # A2: Division by zero checks
    division_pattern = re.compile(r'/\s*(\w+[\[\]]*)')
    for i, line in enumerate(lines, 1):
        if '/' in line and not line.strip().startswith('//'):
            # Look for division operations
            if re.search(r'\w+\s*/\s*\w+', line):
                # Check if there's a guard
                if 'nz(' not in code[max(0, code.find(lines[i-1])-200):code.find(lines[i-1])+200]:
                    if any(risky in line for risky in ['atr', 'volume', 'close[', 'rthClose', 'range']):
                        issues.append({
                            'category': 'Logical Sanity',
                            'check': 'Division Safety (A2)',
                            'severity': 'CRITICAL',
                            'message': 'Division by potentially zero or na value without guard. Use nz() or check for != 0',
                            'line': i,
                            'code': line.strip()
                        })
    
    # B1: strategy.entry direction check
    if 'strategy.entry' in code:
        entry_pattern = re.compile(r'strategy\.entry\([^,]+,\s*(\w+[\.\w]*)')
        for i, line in enumerate(lines, 1):
            matches = entry_pattern.findall(line)
            for match in matches:
                if match not in ['strategy.long', 'strategy.short']:
                    issues.append({
                        'category': 'Logical Sanity',
                        'check': 'strategy.entry Direction (B1)',
                        'severity': 'CRITICAL',
                        'message': f'strategy.entry must use strategy.long or strategy.short, not "{match}"',
                        'line': i,
                        'code': line.strip()
                    })
    
    # B4: request.security without explicit parameters
    if 'request.security' in code:
        for i, line in enumerate(lines, 1):
            if 'request.security' in line:
                # Check if lookahead is specified
                context_lines = '\n'.join(lines[max(0,i-2):min(len(lines),i+2)])
                if 'barmerge.lookahead' not in context_lines:
                    issues.append({
                        'category': 'Logical Sanity',
                        'check': 'request.security Explicitness (B4)',
                        'severity': 'CRITICAL',
                        'message': 'request.security must have explicit lookahead parameter (barmerge.lookahead_off)',
                        'line': i,
                        'code': line.strip()
                    })
                if 'barmerge.gaps' not in context_lines:
                    issues.append({
                        'category': 'Logical Sanity',
                        'check': 'request.security Gaps Handling (B4)',
                        'severity': 'CRITICAL',
                        'message': 'request.security must have explicit gaps parameter (barmerge.gaps_off)',
                        'line': i,
                        'code': line.strip()
                    })
    
    # C1/C2: Stop/Target direction checks (simplified)
    if 'strategy.exit' in code:
        for i, line in enumerate(lines, 1):
            if 'strategy.exit' in line and 'stop=' in line:
                # Look for context about position direction
                context = '\n'.join(lines[max(0,i-10):min(len(lines),i+2)])
                if 'strategy.position_size > 0' in context:
                    # Long position - stop should be below (subtraction)
                    if '+' in line and 'stop=' in line.split('#')[0]:
                        issues.append({
                            'category': 'Logical Sanity',
                            'check': 'Stop Direction - Long (C1)',
                            'severity': 'CRITICAL',
                            'message': 'Long position stop should be BELOW entry (use subtraction, not addition)',
                            'line': i,
                            'code': line.strip()
                        })
    
    # D1: Check for var without reset logic
    # Exclude UI objects (table, label, line, box) as they persist and don't need resets
    var_pattern = re.compile(r'var\s+(\w+)\s+(\w+)\s*=')
    ui_types = {'table', 'label', 'line', 'box', 'linefill', 'polyline'}
    vars_found = []
    for i, line in enumerate(lines, 1):
        matches = var_pattern.findall(line)
        for var_type, var_name in matches:
            # Skip UI/drawing objects - they don't need session resets
            if var_type.lower() not in ui_types:
                vars_found.append((var_name, i))
    
    for var_name, line_num in vars_found:
        # Check if there's a reset for this var
        reset_pattern = re.compile(rf'{var_name}\s*:=\s*(?:na|0|false)')
        if not reset_pattern.search(code):
            issues.append({
                'category': 'Logical Sanity',
                'check': 'Variable Reset Logic (D1)',
                'severity': 'HIGH',
                'message': f'var "{var_name}" has no reset logic. All var declarations should reset at session boundary or when flat',
                'line': line_num
            })
    
    # ============================================================================
    # 5A. PINE SCRIPT INDENTATION CHECKS
    # ============================================================================
    
    # Check for if statements without proper indentation
    for i in range(len(lines) - 1):
        line = lines[i]
        stripped = line.strip()
        
        # Skip comments
        if stripped.startswith('//') or stripped.startswith('/*'):
            continue
        
        # Check if this is a control statement
        is_control_statement = (
            stripped.startswith('if ') or 
            stripped.startswith('else if ') or
            (stripped == 'else' or stripped.startswith('else '))
        )
        
        if is_control_statement:
            # Get the indentation level of the control statement
            control_indent = len(line) - len(line.lstrip())
            
            # Check the next non-empty, non-comment line
            next_idx = i + 1
            while next_idx < len(lines):
                next_line = lines[next_idx]
                next_stripped = next_line.strip()
                
                # Skip empty lines and comments
                if not next_stripped or next_stripped.startswith('//'):
                    next_idx += 1
                    continue
                
                # Check indentation
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line is not indented more than control statement, flag it
                if next_indent <= control_indent:
                    issues.append({
                        'category': 'Script Structure',
                        'check': 'Indentation (CRITICAL)',
                        'severity': 'CRITICAL',
                        'message': f'Line after "{stripped[:30]}..." must be indented. Pine Script requires indented blocks.',
                        'line': next_idx + 1,
                        'code': next_line.strip()[:60]
                    })
                break
    
    # ============================================================================
    # 5B. PINE SCRIPT V6 SYNTAX CHECKS
    # ============================================================================
    
    # Check for camelCase strategy properties (should be snake_case in v6)
    pine_v6_property_issues = {
        'strategy.positionSize': 'strategy.position_size',
        'strategy.openTrades': 'strategy.open_trades',
        'strategy.closedTrades': 'strategy.closed_trades',
        'strategy.eventTrades': 'strategy.event_trades',
        'strategy.grossProfit': 'strategy.gross_profit',
        'strategy.grossLoss': 'strategy.gross_loss',
        'strategy.netProfit': 'strategy.net_profit',
        'strategy.maxDrawdown': 'strategy.max_drawdown',
        'strategy.initialCapital': 'strategy.initial_capital',
    }
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('//'):
            continue
        
        for old_prop, new_prop in pine_v6_property_issues.items():
            if old_prop in line:
                issues.append({
                    'category': 'Pine Script v6 Syntax',
                    'check': 'Property Names',
                    'severity': 'CRITICAL',
                    'message': f'Use "{new_prop}" instead of "{old_prop}" (Pine Script v6 requires snake_case)',
                    'line': i,
                    'code': line.strip()[:80]
                })
    
    # Check for camelCase strategy() parameters (should be snake_case in v6)
    pine_v6_param_issues = {
        'initialCapital': 'initial_capital',
        'defaultQtyValue': 'default_qty_value',
        'defaultQtyType': 'default_qty_type',
        'commissionType': 'commission_type',
        'commissionValue': 'commission_value',
        'calcOnOrderFills': 'calc_on_order_fills',
        'calcOnEveryTick': 'calc_on_every_tick',
        'maxBarsBack': 'max_bars_back',
        'backTestFillLimitsAssumption': 'backtest_fill_limits_assumption',
        'defaultQtyValuePercentage': 'default_qty_value_percentage',
        'riskFreeRate': 'risk_free_rate',
        'useBarsBacktest': 'use_bars_backtest',
        'fillOrdersOnOpen': 'fill_orders_on_open',
        'processOrdersOnClose': 'process_orders_on_close',
        'closeEntriesRule': 'close_entries_rule',
    }
    
    in_strategy_declaration = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Detect strategy() declaration
        if 'strategy(' in line:
            in_strategy_declaration = True
        
        if in_strategy_declaration:
            for old_param, new_param in pine_v6_param_issues.items():
                # Match parameter with = after it
                if re.search(r'\b' + old_param + r'\s*=', line):
                    issues.append({
                        'category': 'Pine Script v6 Syntax',
                        'check': 'Strategy Parameters',
                        'severity': 'CRITICAL',
                        'message': f'Use "{new_param}=" instead of "{old_param}=" in strategy() declaration (Pine Script v6 requires snake_case)',
                        'line': i,
                        'code': line.strip()[:80]
                    })
        
        # End of strategy declaration
        if in_strategy_declaration and ')' in line:
            in_strategy_declaration = False
    
    # ============================================================================
    # 6. PASS CHECKS (What's Done Well)
    # ============================================================================
    
    # Check for proper type declarations
    if re.search(r'(float|int|bool|string)\s+\w+\s*=', code):
        issues.append({
            'category': 'Formatting',
            'check': 'Explicit Type Declarations',
            'severity': 'PASS',
            'message': 'Using explicit type declarations ✓'
        })
    
    # Check for input grouping
    if code.count('input.') >= 2:
        input_section = re.search(r'//.*Inputs\n(.*?)//.*\n', code, re.DOTALL)
        if input_section:
            issues.append({
                'category': 'Script Structure',
                'check': 'Input Organization',
                'severity': 'PASS',
                'message': 'Inputs are organized in dedicated section ✓'
            })
    
    # ============================================================================
    # 7. RECOMMENDATIONS
    # ============================================================================
    
    if not any('Division Safety' in i['check'] for i in issues if i['severity'] == 'CRITICAL'):
        recommendations.append('Consider adding guard checks (nz() or != 0) for all division operations')
    
    if 'ta.' in code and not any('ta.* Function Scoping' in i['check'] for i in issues):
        recommendations.append('Good: All ta.* functions are called at global scope')
    
    if len([i for i in issues if i['severity'] == 'CRITICAL']) == 0:
        recommendations.append('Code passes all critical checks! Consider reviewing warnings for optimization')
    
    recommendations.append('Refer to /docs/PINE_SCRIPT_STANDARDS.md for complete coding standards')
    recommendations.append('Refer to /docs/LOGICAL_SANITY_CHECKS.md for detailed validation rules')
    
    return {
        'scriptName': script_name,
        'issues': issues,
        'recommendations': recommendations,
        'summary': {
            'total': len(issues),
            'critical': len([i for i in issues if i['severity'] == 'CRITICAL']),
            'high': len([i for i in issues if i['severity'] == 'HIGH']),
            'warning': len([i for i in issues if i['severity'] == 'WARNING']),
            'passed': len([i for i in issues if i['severity'] == 'PASS'])
        }
    }


def to_camel_case(snake_str):
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


@app.route('/api/scripts/<script_id>/save-code', methods=['POST'])
def save_edited_code(script_id):
    """Save edited code and create new version"""
    try:
        request_data = request.json or {}
        edited_code = request_data.get('code')
        changelog = request_data.get('changelog', 'Manual edit via web interface')
        author = request_data.get('author', 'user')
        is_initial_save = request_data.get('isInitialSave', False)
        
        if not edited_code:
            return jsonify({"error": "No code provided"}), 400
        
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Auto-migrate to versioning if needed
        if 'versions' not in script or len(script.get('versions', [])) == 0:
            migrate_script_to_versioning(script)
        
        # Get current version
        current_version = script.get('currentVersion', '1.0.0')
        
        # Check if current code is still the initial template
        current_code, _ = get_version_code(script, current_version)
        is_initial_template = False
        if current_code:
            # Check if it's the initial template (contains the creation marker)
            is_initial_template = "This Pine Script was created via Pine Script Library" in current_code
        
        # If this is the initial template or explicitly marked as initial save, update v1.0.0 in place
        if is_initial_template or (is_initial_save and current_version == '1.0.0'):
            # Update the existing v1.0.0 file instead of creating a new version
            version_to_update = current_version
            
            # Update/inject version header with full metadata
            project_name = get_project_name_from_path(script.get('filePath'))
            filename = f"{project_name}_v{version_to_update}.pine"
            edited_code = update_version_in_code(
                edited_code, 
                version_to_update,
                script_name=script.get('name', 'Unknown Script'),
                script_type=script.get('type', 'indicator').upper(),
                filename=filename,
                changelog='Initial version',
                author=script.get('author', 'Your Name')
            )
            
            # Get the current version file path
            version_file = None
            for v in script.get('versions', []):
                if v['version'] == version_to_update and v.get('isActive'):
                    version_file = Path(v['filePath'])
                    break
            
            if not version_file:
                return jsonify({"error": "Could not find version file"}), 404
            
            # Write the code to the existing file
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(edited_code)
            
            # Update the version entry with new metadata
            for v in script.get('versions', []):
                if v['version'] == version_to_update:
                    v['dateModified'] = datetime.utcnow().isoformat() + 'Z'
                    v['changelog'] = 'Initial version'
                    v['author'] = author
                    break
            
            # Update script metadata
            script['dateModified'] = datetime.utcnow().isoformat() + 'Z'
            
            # Save scripts metadata
            script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
            if script_index is not None:
                data['scripts'][script_index] = script
                save_scripts(data)
            
            return jsonify({
                'success': True,
                'newVersion': version_to_update,
                'previousVersion': version_to_update,
                'changelog': 'Initial version',
                'isInitialVersion': True,
                'message': f'Successfully saved initial version {version_to_update}'
            })
        
        # Otherwise, create a new version (normal edit flow)
        new_version = increment_version(current_version)
        
        # Note: version header will be injected by create_new_version()
        
        # Create new version
        success, version_info, error = create_new_version(
            script,
            new_version,
            edited_code,
            changelog,
            author=author
        )
        
        if not success:
            return jsonify({"error": error or "Failed to create new version"}), 500
        
        # Find and update script in data
        script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
        if script_index is not None:
            data['scripts'][script_index] = script
            save_scripts(data)
        
        return jsonify({
            'success': True,
            'newVersion': new_version,
            'previousVersion': current_version,
            'changelog': changelog,
            'versionInfo': version_info,
            'isInitialVersion': False,
            'message': f'Successfully saved code as version {new_version}'
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>/autofix', methods=['POST'])
def autofix_script_code(script_id):
    """Automatically fix common code issues and create new version"""
    try:
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Auto-migrate to versioning if needed
        if 'versions' not in script or len(script.get('versions', [])) == 0:
            migrate_script_to_versioning(script)
        
        # Get current version's code
        current_version = script.get('currentVersion', '1.0.0')
        code, error = get_version_code(script, current_version)
        
        if error:
            return jsonify({"error": error}), 404
        
        # Run code review BEFORE fixes to identify issues
        review_before = perform_code_review(code, script['name'])
        issues_before = review_before['issues']
        
        # Identify unfixable critical issues BEFORE attempting fixes
        critical_issues = [i for i in issues_before if i['severity'] == 'CRITICAL']
        unfixable_issues = [i for i in critical_issues 
                           if 'ta.*' in i.get('check', '') or 'Function Scoping' in i.get('check', '')]
        
        # If ONLY unfixable issues exist, don't run QuickFix
        fixable_issues = [i for i in issues_before if i not in unfixable_issues and i['severity'] != 'PASS']
        
        if len(fixable_issues) == 0 and len(unfixable_issues) > 0:
            return jsonify({
                'success': False,
                'message': f'All {len(unfixable_issues)} critical issue(s) require Smart Fix (code restructuring needed)',
                'unfixableIssues': [{
                    'check': i.get('check'),
                    'line': i.get('line'),
                    'message': i.get('message'),
                    'code': i.get('code', '')[:80]
                } for i in unfixable_issues],
                'criticalIssuesRemaining': len(critical_issues),
                'recommendSmartFix': True,
                'requiresSmartFix': True
            })
        
        # Apply auto-fixes
        fixed_code, fixes_applied = apply_auto_fixes(code)
        
        # Verify fixes actually changed something
        if fixed_code.strip() == code.strip():
            fixes_applied = []  # No real changes made
        
        # Check if there are still CRITICAL issues after quick fix
        review_after_fix = perform_code_review(fixed_code, script['name'])
        critical_issues_remaining = [i for i in review_after_fix['issues'] if i['severity'] == 'CRITICAL']
        
        # Only create new version if fixes were actually applied
        if len(fixes_applied) == 0:
            return jsonify({
                'success': False,
                'message': 'No fixable issues found (code is already compliant or requires Smart Fix)',
                'unfixableIssues': [{
                    'check': i.get('check'),
                    'line': i.get('line'),
                    'message': i.get('message'),
                    'code': i.get('code', '')[:80]
                } for i in unfixable_issues],
                'criticalIssuesRemaining': len(critical_issues_remaining),
                'recommendSmartFix': len(unfixable_issues) > 0,
                'requiresSmartFix': len(unfixable_issues) > 0
            })
        
        # Increment version
        new_version = increment_version(current_version)
        
        # Note: version header will be injected by create_new_version()
        
        # Create changelog
        changelog = f"Auto-fix: {len(fixes_applied)} issue(s) fixed - " + ", ".join(fixes_applied[:3])
        if len(fixes_applied) > 3:
            changelog += f" (+{len(fixes_applied) - 3} more)"
        
        # Create new version
        success, version_info, error = create_new_version(
            script, 
            new_version, 
            fixed_code, 
            changelog, 
            author='autofix'
        )
        
        if not success:
            return jsonify({"error": error or "Failed to create new version"}), 500
        
        # Find and update script in data
        script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
        if script_index is not None:
            data['scripts'][script_index] = script
            save_scripts(data)
        
        return jsonify({
            'success': True,
            'fixedIssues': len(fixes_applied),
            'fixes': fixes_applied,
            'newVersion': new_version,
            'previousVersion': current_version,
            'changelog': changelog,
            'versionInfo': version_info,
            'criticalIssuesRemaining': len(critical_issues_remaining),
            'unfixableCriticalIssues': len(unfixable_issues),
            'recommendSmartFix': len(unfixable_issues) > 0,
            'warning': f"{len(unfixable_issues)} CRITICAL issue(s) require Smart Fix (ta.* scoping needs code restructuring)" if len(unfixable_issues) > 0 else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/debug/api-key-status', methods=['GET'])
def debug_api_key_status():
    """Debug endpoint to check if server has API key configured"""
    has_key = OPENAI_API_KEY is not None and len(OPENAI_API_KEY) > 0
    key_preview = OPENAI_API_KEY[-10:] if has_key else "No key"
    return jsonify({
        'hasKey': has_key,
        'keyPreview': f"...{key_preview}" if has_key else "Not configured",
        'provider': DEFAULT_LLM_PROVIDER,
        'model': OPENAI_MODEL
    })


@app.route('/api/scripts/<script_id>/auto-fix-all', methods=['POST'])
def auto_fix_all_script(script_id):
    """Apply hybrid auto-fix: Quick Fix first, then Smart Fix on remaining issues"""
    try:
        request_data = request.json or {}
        api_key = request_data.get('apiKey')
        provider = request_data.get('provider', 'openai')
        version = request_data.get('version')
        
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Auto-migrate to versioning if needed
        if 'versions' not in script or len(script.get('versions', [])) == 0:
            migrate_script_to_versioning(script)
        
        # Get current version info
        current_version = version or script.get('currentVersion', '1.0.0')
        
        # Get code for the version
        code, error = get_version_code(script, current_version)
        
        if error:
            return jsonify({"error": error}), 404
        
        # STEP 1: Apply Quick Fix (regex-based)
        quick_fixed_code, quick_fixes = apply_auto_fixes(code)
        
        # STEP 2: Run code review on quick-fixed code
        review_results = perform_code_review(quick_fixed_code, script['name'])
        critical_high_count = review_results['summary']['critical'] + review_results['summary']['high']
        
        # STEP 3: Apply Smart Fix if there are still critical/high issues
        smart_fixes_applied = False
        smart_explanation = ""
        final_code = quick_fixed_code
        
        if critical_high_count > 0:
            fixed_code, explanation, success, error_msg = apply_smart_fixes_with_llm(
                quick_fixed_code,
                script['name'],
                review_results['issues'],
                api_key=api_key,
                provider=provider
            )
            
            if success:
                final_code = fixed_code
                smart_fixes_applied = True
                smart_explanation = explanation
        
        # Increment version
        new_version = increment_version(current_version)
        
        # Note: version header will be injected by create_new_version()
        
        # Create changelog
        changelog_parts = []
        if len(quick_fixes) > 0:
            changelog_parts.append(f"Quick Fix: {len(quick_fixes)} issue(s)")
        if smart_fixes_applied:
            changelog_parts.append(f"Smart Fix: {critical_high_count} critical/high issue(s)")
        
        changelog = f"Auto-Fix All: {', '.join(changelog_parts)}"
        
        # Create new version
        version_success, version_info, version_error = create_new_version(
            script,
            new_version,
            final_code,
            changelog,
            author='auto-fix-all'
        )
        
        if not version_success:
            return jsonify({"error": version_error or "Failed to create new version"}), 500
        
        # Update script in data
        script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
        if script_index is not None:
            data['scripts'][script_index] = script
            save_scripts(data)
        
        return jsonify({
            'success': True,
            'newVersion': new_version,
            'previousVersion': current_version,
            'changelog': changelog,
            'quickFixesApplied': len(quick_fixes),
            'smartFixApplied': smart_fixes_applied,
            'criticalHighIssuesAddressed': critical_high_count if smart_fixes_applied else 0,
            'quickFixes': quick_fixes[:5],  # Show first 5
            'smartExplanation': smart_explanation,
            'versionInfo': version_info,
            'message': f'Successfully applied hybrid fixes as version {new_version}'
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>/smart-autofix', methods=['POST'])
def smart_autofix_script(script_id):
    """Apply intelligent auto-fixes using LLM"""
    try:
        request_data = request.json or {}
        api_key = request_data.get('apiKey')  # Optional user-provided API key
        provider = request_data.get('provider', 'openai')
        version = request_data.get('version')  # Optional: specific version to fix
        
        # Debug logging
        print(f"DEBUG: Client provided API key: {api_key[-10:] if api_key else 'None'}")
        print(f"DEBUG: Server API key: {OPENAI_API_KEY[-10:] if OPENAI_API_KEY else 'None'}")
        
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Auto-migrate to versioning if needed
        if 'versions' not in script or len(script.get('versions', [])) == 0:
            migrate_script_to_versioning(script)
        
        # Get current version info
        current_version = version or script.get('currentVersion', '1.0.0')
        
        # Get code for the version
        code, error = get_version_code(script, current_version)
        
        if error:
            return jsonify({"error": error}), 404
        
        # Step 1: Run code review to get issues
        review_results = perform_code_review(code, script['name'])
        issues = review_results['issues']
        
        if review_results['summary']['critical'] == 0 and review_results['summary']['high'] == 0:
            return jsonify({
                'success': True,
                'message': 'No critical or high-priority issues found',
                'skipped': True
            })
        
        # Step 2: Apply basic regex fixes first
        code, basic_fixes = apply_auto_fixes(code)
        
        # Step 3: Apply LLM-powered smart fixes
        fixed_code, explanation, success, error_msg = apply_smart_fixes_with_llm(
            code, 
            script['name'], 
            issues,
            api_key=api_key,
            provider=provider
        )
        
        if not success:
            return jsonify({
                "error": f"LLM fix failed: {error_msg}",
                "basicFixesApplied": len(basic_fixes),
                "basicFixes": basic_fixes
            }), 500
        
        # Increment version
        new_version = increment_version(current_version)
        
        # Note: version header will be injected by create_new_version()
        
        # Create changelog
        changelog = f"Smart Auto-fix (LLM): Fixed {review_results['summary']['critical']} critical and {review_results['summary']['high']} high-priority issues. {explanation[:100]}"
        
        # Create new version
        version_success, version_info, version_error = create_new_version(
            script, 
            new_version, 
            fixed_code, 
            changelog, 
            author='smart-autofix'
        )
        
        if not version_success:
            return jsonify({"error": version_error or "Failed to create new version"}), 500
        
        # Update script in data
        script_index = next((i for i, s in enumerate(data['scripts']) if s['id'] == script_id), None)
        if script_index is not None:
            data['scripts'][script_index] = script
            save_scripts(data)
        
        return jsonify({
            'success': True,
            'newVersion': new_version,
            'previousVersion': current_version,
            'changelog': changelog,
            'explanation': explanation,
            'basicFixesApplied': len(basic_fixes),
            'issuesAddressed': review_results['summary']['critical'] + review_results['summary']['high'],
            'versionInfo': version_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def apply_auto_fixes(code):
    """
    Apply automated fixes to Pine Script code
    Returns: (fixed_code, list_of_fixes_applied)
    """
    fixes_applied = []
    lines = code.split('\n')
    
    # ============================================================================
    # FIRST PASS: Fix ternary operator line continuation (CRITICAL - causes syntax errors)
    # ============================================================================
    # When a line ends with ?, the next line must be indented
    in_multiline_comment = False
    ternary_fixes = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            i += 1
            continue
        
        # Skip comments
        if stripped.startswith('//') or in_multiline_comment:
            i += 1
            continue
        
        # Check if line ends with an operator that requires continuation indentation
        # Pine Script requires indentation for line continuation with ANY operator
        continuation_operators = [
            '?',      # Ternary operator
            'and',    # Logical AND
            'or',     # Logical OR
            '+',      # Addition
            '-',      # Subtraction
            '*',      # Multiplication
            '/',      # Division
            '==',     # Equality
            '!=',     # Not equal
            '>',      # Greater than
            '<',      # Less than
            '>=',     # Greater or equal
            '<=',     # Less or equal
        ]
        
        # Check for operators at end of line
        is_operator_continuation = False
        for op in continuation_operators:
            if stripped.endswith(op):
                is_operator_continuation = True
                break
        
        # Special case: line has ? and ends with :
        if not is_operator_continuation and stripped.endswith(':') and '?' in stripped:
            is_operator_continuation = True
        
        if is_operator_continuation:
            # Find next non-empty, non-comment line
            next_idx = i + 1
            while next_idx < len(lines):
                next_line = lines[next_idx]
                next_stripped = next_line.strip()
                
                # Skip empty lines and comments
                if not next_stripped or next_stripped.startswith('//'):
                    next_idx += 1
                    continue
                
                # Found continuation line - check indentation
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If not indented properly, fix it
                if next_indent <= current_indent:
                    # Continuation line needs to be indented 4 spaces MORE than the line with operator
                    required_indent = current_indent + 4
                    # Strip existing leading whitespace and add correct indentation
                    lines[next_idx] = (' ' * required_indent) + next_stripped
                    ternary_fixes += 1
                    fixes_applied.append(f"Line {next_idx+1}: Fixed operator line continuation (added indentation)")
                
                break
        
        i += 1
    
    if ternary_fixes > 0:
        fixes_applied.append(f"Fixed {ternary_fixes} ternary operator line continuation issue(s)")
    
    # ============================================================================
    # SECOND PASS: Identify input variables that need Input suffix
    # ============================================================================
    input_renames = {}  # Maps old_name -> new_name
    input_pattern = re.compile(r'(\w+)\s*=\s*input\.(bool|int|float|string|color|time|timeframe|source|session)')
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*'):
            continue
        
        matches = input_pattern.findall(line)
        for var_name, input_type in matches:
            if not var_name.endswith('Input'):
                new_name = var_name + 'Input'
                input_renames[var_name] = new_name
                fixes_applied.append(f"Line {i}: Renamed input variable '{var_name}' to '{new_name}'")
    
    # ============================================================================
    # THIRD PASS: Apply all other fixes line by line
    # ============================================================================
    fixed_lines = []
    
    # Track multi-line comment blocks
    in_multiline_comment = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        original_line = line
        stripped = line.strip()
        
        # Track multi-line comment state
        if '/*' in line:
            in_multiline_comment = True
        if '*/' in line:
            in_multiline_comment = False
            fixed_lines.append(line)
            i += 1
            continue
        
        # Note: We no longer auto-upgrade v5 to v6 (both versions are acceptable)
        # Fix version BEFORE skipping comments (since version directive is a comment)
        # if i < 5 and '//@version=5' in line:
        #     line = line.replace('//@version=5', '//@version=6')
        #     fixes_applied.append(f"Line {i+1}: Upgraded Pine Script version from 5 to 6")
        
        # Skip single-line comments and multi-line comment blocks
        if stripped.startswith('//') or in_multiline_comment:
            fixed_lines.append(line)
            i += 1
            continue
        
        # Fix 1: Add spaces around operators
        if '=' in line:
            # Fix assignment operators without spaces (match multiple characters)
            # Note: These will add spaces everywhere, but Fix 11 later removes them from function parameters
            line = re.sub(r'([a-zA-Z0-9_]+)=([a-zA-Z0-9_])', r'\1 = \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+)\+=([a-zA-Z0-9_])', r'\1 += \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+)-=([a-zA-Z0-9_])', r'\1 -= \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+)\*=([a-zA-Z0-9_])', r'\1 *= \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+)/=([a-zA-Z0-9_])', r'\1 /= \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+):=([a-zA-Z0-9_])', r'\1 := \2', line)
            
            # Fix arithmetic operators (match multiple characters)
            line = re.sub(r'([a-zA-Z0-9_]+)\+([a-zA-Z0-9_])', r'\1 + \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+)-([a-zA-Z0-9_])', r'\1 - \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+)\*([a-zA-Z0-9_])', r'\1 * \2', line)
            line = re.sub(r'([a-zA-Z0-9_]+)/([a-zA-Z0-9_])', r'\1 / \2', line)
        
        # Fix 1b: Add spaces around comparison operators (avoid breaking >=, <=, ==, !=)
        # Do this AFTER assignment operators to avoid conflicts
        if '>' in line or '<' in line:
            # Fix > and < (but not >= or <=)
            line = re.sub(r'([a-zA-Z0-9_\]]+)>(?!=)([a-zA-Z0-9_\[])', r'\1 > \2', line)
            line = re.sub(r'([a-zA-Z0-9_\]]+)<(?!=)([a-zA-Z0-9_\[])', r'\1 < \2', line)
        
        # Fix 1c: Multi-line if statement indentation
        # Check if this is an if statement without inline body
        if re.match(r'^(\s*)(if|else\s+if)\s+.+$', stripped) and not '=>' in line:
            # Look ahead to see if next line needs indentation
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_stripped = next_line.strip()
                
                # Skip empty lines
                peek_idx = i + 1
                while peek_idx < len(lines) and not lines[peek_idx].strip():
                    peek_idx += 1
                
                if peek_idx < len(lines):
                    next_line = lines[peek_idx]
                    next_stripped = next_line.strip()
                    
                    # Check indentation
                    if next_stripped and not next_stripped.startswith('//'):
                        current_indent = len(line) - len(line.lstrip())
                        next_indent = len(next_line) - len(next_line.lstrip())
                        
                        # If next line is not indented, it needs fixing
                        if next_indent <= current_indent and not re.match(r'^(if|else|var|const|float|int|bool|string)', next_stripped):
                            # Mark that we need to indent the following lines
                            # This will be handled in a separate pass below
                            pass
        
        if line != original_line:
            fixes_applied.append(f"Line {i+1}: Added operator spacing")
        
        # Fix 2: Apply input variable renames throughout the code
        # Replace all occurrences of renamed input variables
        for old_name, new_name in input_renames.items():
            # Use word boundaries to avoid partial matches
            # Match: old_name followed by space, operator, or end of identifier
            pattern = r'\b' + re.escape(old_name) + r'\b'
            if re.search(pattern, line):
                line = re.sub(pattern, new_name, line)
        
        # Fix 3: Convert snake_case variables to camelCase (cautiously)
        # Only fix simple variable assignments, not constants or function parameters
        if '=' in line and not 'const' in line and not line.strip().startswith('//'):
            # Find snake_case variable names
            snake_case_pattern = re.compile(r'\b([a-z]+_[a-z_]+)\s*=(?!=|<|>)')
            matches = snake_case_pattern.findall(line)
            for match in matches:
                # Skip constants (all uppercase)
                if match.isupper():
                    continue
                
                # Skip 'input' keyword itself
                if 'input' in match.lower():
                    continue
                
                # Skip function parameters (appear after ( or , within function calls)
                # Example: strategy(..., initial_capital=50000) should NOT be converted
                if re.search(r'[(,]\s*[^)]*\b' + re.escape(match) + r'\s*=', line):
                    continue
                
                # Convert to camelCase
                camel_case = to_camel_case(match)
                line = line.replace(match + ' =', camel_case + ' =')
                fixes_applied.append(f"Line {i+1}: Converted '{match}' to '{camel_case}'")
        
        # Fix 5: Type mismatch corrections
        # ta.change() returns int, not bool
        if 'bool' in line and 'ta.change(' in line and '=' in line:
            original = line
            # Change bool to int for ta.change()
            line = re.sub(r'\b(const\s+)?bool\b', r'\1int', line)
            if line != original:
                fixes_applied.append(f"Line {i+1}: Changed 'bool' to 'int' for ta.change() return type")
        
        # na() returns bool, not int/float
        if ('int' in line or 'float' in line) and 'na(' in line and '=' in line:
            original = line
            # Change int/float to bool for na()
            line = re.sub(r'\b(const\s+)?(?:int|float)\b', r'\1bool', line)
            if line != original:
                fixes_applied.append(f"Line {i+1}: Changed to 'bool' for na() return type")
        
        # ta.crossover/crossunder return bool, not int/float
        if ('int' in line or 'float' in line) and ('ta.crossover(' in line or 'ta.crossunder(' in line) and '=' in line:
            original = line
            line = re.sub(r'\b(const\s+)?(?:int|float)\b', r'\1bool', line)
            if line != original:
                fixes_applied.append(f"Line {i+1}: Changed to 'bool' for ta.crossover()/ta.crossunder() return type")
        
        # ta.pivothigh/pivotlow return float, not bool
        if 'bool' in line and ('ta.pivothigh(' in line or 'ta.pivotlow(' in line) and '=' in line:
            original = line
            line = re.sub(r'\b(const\s+)?bool\b', r'\1float', line)
            if line != original:
                fixes_applied.append(f"Line {i+1}: Changed 'bool' to 'float' for ta.pivot*() return type")
        
        # ta.barssince returns int, not bool
        if 'bool' in line and 'ta.barssince(' in line and '=' in line:
            original = line
            line = re.sub(r'\b(const\s+)?bool\b', r'\1int', line)
            if line != original:
                fixes_applied.append(f"Line {i+1}: Changed 'bool' to 'int' for ta.barssince() return type")
        
        # Fix 6: ta.* scoping issues CANNOT be automatically fixed
        # These require code restructuring (moving ta.* calls to global scope)
        # Use Smart Fix (LLM) for these issues instead
        # REMOVED: Adding warning comments doesn't fix the issue and confuses users
        
        # Fix 7: Add //@version=5 if missing (v5 is widely supported)
        if i == 0 and '//@version=' not in code[:100]:
            fixed_lines.append('//@version=5')
            fixes_applied.append("Added //@version=5 declaration")
        
        # Fix 8: Remove spaces in session/timezone/timestamp strings
        if 'const string' in line or 'timestamp(' in line or 'input.time(' in line:
            original = line
            # Fix session strings: "0930 - 1600" -> "0930-1600"
            line = re.sub(r'"\s*(\d{4})\s*-\s*(\d{4})\s*:', r'"\1-\2:', line)
            # Fix timezone strings: "America / New_York" -> "America/New_York"
            line = re.sub(r'"([A-Za-z_]+)\s*/\s*([A-Za-z_]+)"', r'"\1/\2"', line)
            # Fix timestamp strings: "2025 - 10 - 01" -> "2025-10-01"
            line = re.sub(r'"\s*(\d{4})\s*-\s*(\d{2})\s*-\s*(\d{2})', r'"\1-\2-\3', line)
            # Fix general strings with " / ": "TP / SL" -> "TP/SL" (but preserve spaces before/after)
            line = re.sub(r'([A-Za-z]+)\s*/\s*([A-Za-z]+)', r'\1/\2', line)
            
            if line != original:
                fixes_applied.append(f"Line {i+1}: Removed invalid spaces in string constants")
        
        # Fix 9: Fix request.security missing parameters
        if 'request.security' in line:
            # Check if this is a complete call or spans multiple lines
            complete_call = line
            line_num = i
            
            # Check if call continues on next lines
            if '(' in line and ')' not in line:
                # Multi-line call, gather all lines
                j = i + 1
                while j < len(lines) and ')' not in complete_call:
                    complete_call += ' ' + lines[j].strip()
                    j += 1
            
            # Check if barmerge parameters are missing
            has_lookahead = 'barmerge.lookahead' in complete_call
            has_gaps = 'barmerge.gaps' in complete_call
            
            if not has_lookahead or not has_gaps:
                # Need to fix this request.security call
                # Find the closing parenthesis position
                if ')' in complete_call:
                    # Count existing parameters
                    paren_start = complete_call.index('(')
                    paren_end = complete_call.rindex(')')
                    params_section = complete_call[paren_start+1:paren_end]
                    
                    # Build the fixed parameters
                    params_to_add = []
                    if not has_gaps:
                        params_to_add.append('barmerge.gaps_off')
                    if not has_lookahead:
                        params_to_add.append('barmerge.lookahead_off')
                    
                    # Add parameters before closing paren
                    additional_params = ', ' + ', '.join(params_to_add)
                    fixed_call = complete_call[:paren_end] + additional_params + complete_call[paren_end:]
                    
                    # If it was a single line, update it
                    if i == line_num and ')' in line:
                        line = fixed_call
                        fixes_applied.append(f"Line {i+1}: Added explicit barmerge parameters to request.security()")
                    else:
                        # Multi-line call - more complex, just add comment for now
                        indent = len(line) - len(line.lstrip())
                        comment = ' ' * indent + '// TODO: Add explicit barmerge.gaps_off and barmerge.lookahead_off parameters\n'
                        fixed_lines.append(comment)
                        fixes_applied.append(f"Line {i+1}: Added TODO comment for request.security() parameters")
        
        fixed_lines.append(line)
        i += 1
    
    fixed_code = '\n'.join(fixed_lines)
    
    # Fix 10: Fix multi-line if statement indentation
    # Pine Script requires multi-line if bodies to be indented
    lines_v10 = fixed_code.split('\n')
    fixed_lines_v10 = []
    if_indent_fixes = 0
    
    i = 0
    while i < len(lines_v10):
        line = lines_v10[i]
        stripped = line.strip()
        
        # Check if this is a multi-line if statement (no => on same line)
        # Match: if/for/while followed by space, else if, or else at end of line
        is_control_stmt = (re.match(r'^(\s*)(if|for|while)\s+', stripped) or 
                          re.match(r'^(\s*)(else\s+if)\s+', stripped) or
                          stripped == 'else' or
                          re.match(r'^(\s*)else\s*$', stripped))
        if is_control_stmt and '=>' not in line and ':' not in line:
            if_indent = len(line) - len(line.lstrip())
            fixed_lines_v10.append(line)
            i += 1
            
            # Check if next line(s) need indenting
            # Skip empty lines and comments
            while i < len(lines_v10):
                next_line = lines_v10[i]
                next_stripped = next_line.strip()
                
                # If empty or comment, keep as-is
                if not next_stripped or next_stripped.startswith('//'):
                    fixed_lines_v10.append(next_line)
                    i += 1
                    continue
                
                # Check indentation of first real line after if
                next_indent = len(next_line) - len(next_line.lstrip())
                expected_indent = if_indent + 4
                
                # If it's not indented by exactly 4 spaces more than the if statement, we need to fix it
                if next_indent != expected_indent:
                    # Check if this is a new statement (another if, var, const, etc) or part of the if body
                    is_new_block = re.match(r'^(if|else|var|const|for|while)\s+', next_stripped)
                    
                    if not is_new_block:
                        # This is the if body that needs indenting
                        # Calculate expected indent (if_indent + 4)
                        expected_body_indent = if_indent + 4
                        
                        # Collect all lines that are part of the body
                        body_lines = []
                        while i < len(lines_v10):
                            body_line = lines_v10[i]
                            body_stripped = body_line.strip()
                            body_indent = len(body_line) - len(body_line.lstrip())
                            
                            # If empty, add and continue
                            if not body_stripped:
                                body_lines.append(body_line)
                                i += 1
                                continue
                            
                            # If it's another control statement at same/less indent, we're done
                            if body_indent < if_indent or (body_indent == if_indent and re.match(r'^(if|else|var|const|for|while)\s+', body_stripped)):
                                break
                            
                            # Check if this line needs re-indenting
                            if body_indent < expected_body_indent:
                                # Not indented enough - fix it
                                # Remove existing indentation and add correct amount
                                spaces_to_add = expected_body_indent - body_indent
                                indented_line = (' ' * spaces_to_add) + body_line
                                body_lines.append(indented_line)
                                if_indent_fixes += 1
                                i += 1
                            elif body_indent == expected_body_indent:
                                # Already correctly indented
                                body_lines.append(body_line)
                                i += 1
                            elif body_indent > expected_body_indent:
                                # More indented (nested code) - keep relative indentation
                                body_lines.append(body_line)
                                i += 1
                            else:
                                break
                        
                        # Add all body lines
                        fixed_lines_v10.extend(body_lines)
                        break  # Done with this if statement
                    else:
                        # It's a new statement, not part of if body
                        break
                else:
                    # Already properly indented
                    break
        else:
            # Not an if statement, keep as-is
            fixed_lines_v10.append(line)
            i += 1
    
    if if_indent_fixes > 0:
        fixes_applied.append(f"Fixed indentation for {if_indent_fixes} if/else statement body line(s)")
        fixed_code = '\n'.join(fixed_lines_v10)
    
    # Fix 11: Ensure proper spacing around commas in function calls
    original_code_joined = '\n'.join(lines)
    fixed_code = re.sub(r',([a-zA-Z0-9_])', r', \1', fixed_code)
    if fixed_code != original_code_joined:
        fixes_applied.append("Added spacing after commas")
    
    # Fix 12: Fix named parameters - remove spaces around = ONLY in function calls
    # This is tricky: we want step = 0.05 -> step=0.05 (in functions)
    # But keep: float x = 5 (variable declarations)
    # Strategy: Only fix parameters that appear after a comma or opening paren
    fixed_code_v2 = fixed_code
    
    # Pattern: After comma or paren: ", step = 0.05" -> ", step=0.05"
    fixed_code_v2 = re.sub(r'([,(])\s*(\w+)\s*=\s*', r'\1 \2=', fixed_code_v2)
    
    if fixed_code_v2 != fixed_code:
        fixes_applied.append("Fixed spacing in named parameters (removed spaces around =)")
        fixed_code = fixed_code_v2
    
    # Fix 13: Ensure variable declarations HAVE spaces around =
    # Pattern: start of line (with optional type/var) followed by identifier=value
    # Examples: "float x=5" -> "float x = 5", "var int y=10" -> "var int y = 10"
    # ONLY flag lines that actually have missing spaces (x=5 not x = 5)
    fixed_code_v3 = fixed_code
    lines_v3 = fixed_code_v3.split('\n')
    fixed_lines_v3 = []
    actual_var_fixes = 0
    
    for line in lines_v3:
        original = line
        # Match variable declarations: optional type keywords, then identifier=value
        # Must be at start of line (after optional whitespace)
        # Pattern: (optional: var/float/int/bool/string/color) identifier=value
        # This regex looks for lines that start with type declaration
        # BUT check if there are ACTUALLY missing spaces (not already correct)
        if re.match(r'^\s*(var\s+)?(float|int|bool|string|color|line|label|box|table|array)\s+\w+\s*=(?!=)', line):
            # Check if spaces are actually missing
            match = re.search(r'(\w+)\s*=\s*(?!=)', line)
            if match:
                var_name = match.group(1)
                # Check if there's NO space before or after =
                if re.search(r'(\w+)=(?!=)', line) or re.search(r'=(\S)', line):
                    # Only replace if this looks like a declaration, not a function parameter
                    if '(' not in line[:match.start()] or line[:match.start()].count('(') == line[:match.start()].count(')'):
                        line = re.sub(r'(\b' + var_name + r')\s*=\s*(?!=)', r'\1 = ', line, count=1)
                        if line != original:
                            actual_var_fixes += 1
        
        fixed_lines_v3.append(line)
    
    fixed_code_v3 = '\n'.join(fixed_lines_v3)
    if fixed_code_v3 != fixed_code and actual_var_fixes > 0:
        fixes_applied.append(f"Added spaces around = in {actual_var_fixes} variable declaration(s)")
        fixed_code = fixed_code_v3
    
    # Fix 14: Fix Pine Script indentation (if blocks must have indented bodies)
    # In Pine Script, if you have multi-line if bodies, they MUST be indented
    lines_v3b = fixed_code.split('\n')
    fixed_lines_v3b = []
    indentation_fixes = 0
    
    i = 0
    while i < len(lines_v3b):
        line = lines_v3b[i]
        stripped = line.strip()
        
        # Check if this is an if/else/for/while statement
        is_control_statement = (
            stripped.startswith('if ') or 
            stripped.startswith('else if ') or 
            stripped.startswith('else ') or
            stripped.startswith('for ') or
            stripped.startswith('while ')
        )
        
        if is_control_statement and not stripped.startswith('//'):
            # Get the indentation level of the control statement
            control_indent = len(line) - len(line.lstrip())
            fixed_lines_v3b.append(line)
            i += 1
            
            # Check the next line(s) - they should be indented
            if i < len(lines_v3b):
                next_line = lines_v3b[i]
                next_stripped = next_line.strip()
                
                # Skip empty lines and comments
                while i < len(lines_v3b) and (not next_stripped or next_stripped.startswith('//')):
                    fixed_lines_v3b.append(next_line)
                    i += 1
                    if i < len(lines_v3b):
                        next_line = lines_v3b[i]
                        next_stripped = next_line.strip()
                
                # Check if next non-empty, non-comment line is indented
                if i < len(lines_v3b) and next_stripped:
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # If next line is not indented more than control statement, it needs fixing
                    if next_indent <= control_indent:
                        # Indent the body lines (collect all lines until we hit a line with same/less indentation)
                        while i < len(lines_v3b):
                            body_line = lines_v3b[i]
                            body_stripped = body_line.strip()
                            
                            # Skip empty lines
                            if not body_stripped:
                                fixed_lines_v3b.append(body_line)
                                i += 1
                                continue
                            
                            body_indent = len(body_line) - len(body_line.lstrip())
                            
                            # Check if this line is part of the body or a new statement
                            # If it starts with a control keyword at same/less indent, we're done
                            is_new_statement = (
                                body_stripped.startswith('if ') or
                                body_stripped.startswith('else') or
                                body_stripped.startswith('for ') or
                                body_stripped.startswith('while ') or
                                body_stripped.startswith('var ') or
                                body_stripped.startswith('const ') or
                                (body_indent <= control_indent and ':=' not in body_line and '=' in body_line)
                            )
                            
                            # If body_indent <= control_indent and it's a new statement, we're done with body
                            if body_indent <= control_indent and is_new_statement:
                                break
                            
                            # Otherwise, ensure this line is indented
                            if body_indent <= control_indent:
                                # Add 2-space indentation
                                fixed_line = ' ' * (control_indent + 2) + body_stripped
                                fixed_lines_v3b.append(fixed_line)
                                indentation_fixes += 1
                                i += 1
                            else:
                                # Already properly indented
                                fixed_lines_v3b.append(body_line)
                                i += 1
                                
                                # Only fix one block of statements (until we hit proper indentation)
                                break
        else:
            fixed_lines_v3b.append(line)
            i += 1
    
    if indentation_fixes > 0:
        fixes_applied.append(f"Fixed indentation for {indentation_fixes} line(s) in if/for/while blocks")
        fixed_code = '\n'.join(fixed_lines_v3b)
    
    # Fix 14: Convert Pine Script v6 strategy property names (camelCase -> snake_case)
    # strategy.positionSize -> strategy.position_size
    pine_v6_properties = {
        'strategy.positionSize': 'strategy.position_size',
        'strategy.openTrades': 'strategy.open_trades',
        'strategy.closedTrades': 'strategy.closed_trades',
        'strategy.eventTrades': 'strategy.event_trades',
        'strategy.wintrades': 'strategy.wintrades',  # No change needed
        'strategy.losstrades': 'strategy.losstrades',  # No change needed
        'strategy.eventrades': 'strategy.eventrades',  # No change needed
        'strategy.grossProfit': 'strategy.gross_profit',
        'strategy.grossLoss': 'strategy.gross_loss',
        'strategy.netProfit': 'strategy.net_profit',
        'strategy.maxDrawdown': 'strategy.max_drawdown',
        'strategy.initialCapital': 'strategy.initial_capital',
    }
    
    fixed_code_v4 = fixed_code
    for old_prop, new_prop in pine_v6_properties.items():
        if old_prop in fixed_code_v4:
            fixed_code_v4 = fixed_code_v4.replace(old_prop, new_prop)
            fixes_applied.append(f"Converted '{old_prop}' to '{new_prop}' (Pine Script v6)")
    
    fixed_code = fixed_code_v4
    
    # Fix 15: Convert strategy() declaration parameters (camelCase -> snake_case)
    # This is more complex because we need to handle multi-line strategy declarations
    strategy_params = {
        'initialCapital': 'initial_capital',
        'defaultQtyValue': 'default_qty_value',
        'defaultQtyType': 'default_qty_type',
        'commissionType': 'commission_type',
        'commissionValue': 'commission_value',
        'pyramiding': 'pyramiding',  # No change
        'calcOnOrderFills': 'calc_on_order_fills',
        'calcOnEveryTick': 'calc_on_every_tick',
        'maxBarsBack': 'max_bars_back',
        'backTestFillLimitsAssumption': 'backtest_fill_limits_assumption',
        'defaultQtyValuePercentage': 'default_qty_value_percentage',
        'riskFreeRate': 'risk_free_rate',
        'useBarsBacktest': 'use_bars_backtest',
        'fillOrdersOnOpen': 'fill_orders_on_open',
        'processOrdersOnClose': 'process_orders_on_close',
        'closeEntriesRule': 'close_entries_rule',
    }
    
    fixed_code_v5 = fixed_code
    lines_v5 = fixed_code_v5.split('\n')
    in_strategy_declaration = False
    strategy_start_line = -1
    
    for i, line in enumerate(lines_v5):
        # Detect start of strategy() declaration
        if 'strategy(' in line:
            in_strategy_declaration = True
            strategy_start_line = i
        
        # If we're in a strategy declaration, apply parameter fixes
        if in_strategy_declaration:
            original_line = line
            for old_param, new_param in strategy_params.items():
                # Match parameter names with = after them (named parameters)
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + old_param + r'\s*='
                if re.search(pattern, line):
                    line = re.sub(pattern, new_param + '=', line)
            
            if line != original_line:
                lines_v5[i] = line
                fixes_applied.append(f"Line {i+1}: Converted strategy() parameter(s) to snake_case (Pine Script v6)")
        
        # Detect end of strategy() declaration
        if in_strategy_declaration and ')' in line:
            in_strategy_declaration = False
    
    fixed_code = '\n'.join(lines_v5)
    
    return fixed_code, fixes_applied


def apply_smart_fixes_with_llm(code, script_name, issues, api_key=None, provider='openai'):
    """
    Apply intelligent fixes using LLM API
    
    Args:
        code: The Pine Script code to fix
        script_name: Name of the script
        issues: List of issues from code review
        api_key: Optional API key (uses server key if not provided)
        provider: 'openai' or 'claude'
    
    Returns:
        (fixed_code, explanation, success, error_message)
    """
    try:
        # Use provided API key or fallback to server configuration
        effective_api_key = api_key or OPENAI_API_KEY
        
        # Initialize manual review issues list
        manual_review_issues = []
        
        if not effective_api_key:
            return (code, "No API key available", False, "API key not configured")
        
        # Load documentation context
        docs_context = ""
        try:
            with open('docs/PINE_SCRIPT_STANDARDS.md', 'r', encoding='utf-8') as f:
                docs_context += f"## Pine Script Standards\n{f.read()}\n\n"
        except:
            pass
        
        try:
            with open('docs/LOGICAL_SANITY_CHECKS.md', 'r', encoding='utf-8') as f:
                docs_context += f"## Logical Sanity Checks\n{f.read()}\n\n"
        except:
            pass
        
        # Filter for CRITICAL and HIGH severity issues only
        critical_issues = [
            issue for issue in issues 
            if issue.get('severity') in ['CRITICAL', 'HIGH']
        ]
        
        if not critical_issues:
            return (code, "No critical or high-priority issues to fix", True, None)
        
        # ============================================================================
        # STEP 1: Ask LLM to identify which issues need special attention
        # ============================================================================
        
        # Build issue summary for evaluation
        issues_list = "\n".join([
            f"{idx+1}. {issue.get('check', 'Unknown')}: {issue.get('message', 'No details')} (Line {issue.get('line', 'N/A')})"
            for idx, issue in enumerate(critical_issues)
        ])
        
        evaluation_prompt = f"""You are reviewing Pine Script code issues to determine which ones you can safely auto-fix and which require manual review.

**Issues to Evaluate:**
{issues_list}

**Code Snippet (first 50 lines):**
```pinescript
{chr(10).join(code.split(chr(10))[:50])}
```

**TASK:**
For each issue, determine if it requires SPECIAL ATTENTION (manual review) or can be SAFELY AUTO-FIXED.

**Issues that typically need SPECIAL ATTENTION:**
1. Variable Reset Logic (D1) - Depends on strategy intent (persistent vs session-based state)
2. Complex business logic decisions - Entry/exit conditions, parameter choices
3. Strategy-specific reset conditions - What triggers a reset depends on trading rules
4. Ambiguous requirements - Multiple valid solutions exist
5. Risk of breaking strategy logic - Could change trading behavior

**Issues that can be SAFELY AUTO-FIXED:**
1. ta.* Function Scoping (B8) - Move to global scope (mechanical fix)
2. Syntax errors - Missing parameters, spacing issues
3. Naming conventions - camelCase, SNAKE_CASE conversions
4. Code organization - Script structure improvements

**OUTPUT FORMAT:**
Return a JSON object with this structure:
{{
  "can_auto_fix": [1, 2, ...],
  "needs_manual_review": [
    {{
      "issue_number": 3,
      "check_name": "Variable Reset Logic (D1)",
      "rationale": "These variables track historical pivots for divergence detection. Whether they should reset depends on if the strategy needs multi-session or single-session divergences. This is a business logic decision.",
      "recommendation": "Review if pivots should persist across sessions or reset daily."
    }}
  ]
}}

Respond with ONLY the JSON, no other text."""

        try:
            # Call LLM for issue evaluation
            if provider == 'openai':
                client = OpenAI(api_key=effective_api_key)
                eval_response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert code reviewer. Analyze which issues require human judgment vs mechanical fixes."},
                        {"role": "user", "content": evaluation_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                eval_result = eval_response.choices[0].message.content.strip()
                
                # Parse JSON response
                import json
                # Extract JSON from markdown code blocks if present
                if '```json' in eval_result:
                    eval_result = re.search(r'```json\n(.*?)\n```', eval_result, re.DOTALL).group(1)
                elif '```' in eval_result:
                    eval_result = re.search(r'```\n(.*?)\n```', eval_result, re.DOTALL).group(1)
                
                evaluation = json.loads(eval_result)
                
                # Store manual review issues in the result for display
                manual_review_issues = evaluation.get('needs_manual_review', [])
                can_fix_indices = evaluation.get('can_auto_fix', [])
                
                # Filter issues to only auto-fix the safe ones
                if can_fix_indices:
                    critical_issues = [critical_issues[i-1] for i in can_fix_indices if 0 < i <= len(critical_issues)]
                
                # If nothing can be auto-fixed, return manual review list
                if not critical_issues and manual_review_issues:
                    manual_review_text = "\n\n".join([
                        f"**{item['check_name']}** (Issue #{item['issue_number']})\n"
                        f"⚠️ **Why it needs attention:** {item['rationale']}\n"
                        f"💡 **Recommendation:** {item['recommendation']}"
                        for item in manual_review_issues
                    ])
                    
                    return (
                        code, 
                        f"⚠️ **All issues require manual review**\n\n{manual_review_text}", 
                        True, 
                        None
                    )
                
        except Exception as e:
            # If evaluation fails, proceed with all issues (fail-safe)
            manual_review_issues = []
            print(f"Issue evaluation failed, proceeding with all issues: {e}")
        
        # Build issue summary for fixing (only safe issues)
        issues_summary = "\n".join([
            f"- {issue.get('check', 'Unknown')}: {issue.get('message', 'No details')} (Line {issue.get('line', 'N/A')})"
            for issue in critical_issues
        ])
        
        # Construct LLM prompt
        system_prompt = """You are an expert Pine Script v5 developer. Your task is to fix code quality issues while preserving trading strategy logic completely.

CRITICAL RULES:
1. NEVER change trading logic, entry/exit conditions, or strategy parameters
2. ONLY fix technical code quality issues (scoping, variable management, syntax)
3. Preserve all comments and documentation
4. Follow Pine Script v5 standards exactly
5. Return ONLY the fixed code, no explanations in the code itself

COMMON FIXES:
**B8 - ta.* Function Scoping**: Move ta.* functions OUTSIDE if blocks to global scope
   BAD:  if condition
             if ta.barssince(x) < 10
   GOOD: barsSinceX = ta.barssince(x)  // At global scope
         if condition
             if barsSinceX < 10

**D1 - Variable Reset**: Add reset logic for var STATE variables (NOT UI objects!)
   UI objects (table, label, line, box) do NOT need resets - skip these!
   BAD:  var float myVar = na  // State variable without reset
   GOOD: var float myVar = na
         if sessionBoundary
             myVar := na
   SKIP: var table myTable = table.new(...)  // UI object - no reset needed"""

        user_prompt = f"""Fix the following Pine Script code based on these CRITICAL/HIGH issues:

{issues_summary}

**Original Code:**
```pinescript
{code}
```

**Documentation Context (first 3000 chars):**
{docs_context[:3000]}

**FIXING INSTRUCTIONS:**

For B8 (ta.* Scoping):
1. Find ALL ta.* function calls inside if/for blocks
2. Move them to global scope BEFORE any if blocks
3. Store result in a descriptively-named variable
4. Use that variable in the if block logic

For D1 (Variable Reset):
1. Find ALL var declarations (EXCEPT UI objects: table, label, line, box)
2. UI objects (table, label, line, box) do NOT need reset logic - they persist by design
3. Add reset logic for STATE variables at appropriate session boundaries (e.g., isFirstBar, not isRth, etc.)

**OUTPUT FORMAT:**
Return the COMPLETE fixed Pine Script code with NO markdown, NO explanations, JUST the code.
After the code, add a blank line then "---EXPLANATION---" then explain what you fixed."""

        # Call OpenAI API
        if provider == 'openai':
            client = OpenAI(api_key=effective_api_key)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            
            # Parse response - expecting code, then ---EXPLANATION---, then explanation
            if '---EXPLANATION---' in result:
                parts = result.split('---EXPLANATION---', 1)
                fixed_code = parts[0].strip()
                explanation = parts[1].strip() if len(parts) > 1 else "Code refactored to fix critical issues."
                
                # Remove any markdown code fences if present
                fixed_code = re.sub(r'^```(?:pinescript)?\n', '', fixed_code)
                fixed_code = re.sub(r'\n```$', '', fixed_code)
                fixed_code = fixed_code.strip()
            else:
                # Fallback: try to extract from code blocks
                code_match = re.search(r'```(?:pinescript)?\n(.*?)```', result, re.DOTALL)
                if code_match:
                    fixed_code = code_match.group(1).strip()
                    explanation = result[code_match.end():].strip()
                    if not explanation:
                        explanation = "Code refactored to fix critical issues."
                else:
                    # No clear format, assume entire response is code
                    fixed_code = result.strip()
                    explanation = "Applied LLM-suggested fixes."
            
            # Validate that we got actual code (should start with // or //@version)
            if not fixed_code.startswith('//@version') and not fixed_code.startswith('//'):
                return (code, "LLM did not return valid Pine Script code", False, "Invalid response format")
            
            # Append manual review issues to explanation if any were flagged
            if manual_review_issues:
                manual_review_text = "\n\n---\n\n## ⚠️ Issues Requiring Manual Review\n\n"
                manual_review_text += "The following issues were **not auto-fixed** because they require human judgment:\n\n"
                
                for item in manual_review_issues:
                    manual_review_text += f"**{item.get('check_name', 'Unknown')}** (Issue #{item.get('issue_number', '?')})\n"
                    manual_review_text += f"- **Why it needs attention:** {item.get('rationale', 'Requires domain expertise')}\n"
                    manual_review_text += f"- **Recommendation:** {item.get('recommendation', 'Review manually')}\n\n"
                
                explanation = explanation + manual_review_text
            
            return (fixed_code, explanation, True, None)
        
        else:
            return (code, "Provider not supported yet", False, "Only OpenAI is currently supported")
    
    except Exception as e:
        return (code, "", False, str(e))


def increment_version(version_string):
    """
    Increment patch version number
    Example: '1.0.0' -> '1.0.1', '1.2.5' -> '1.2.6'
    """
    try:
        parts = version_string.split('.')
        if len(parts) == 3:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            patch += 1
            return f"{major}.{minor}.{patch}"
        else:
            # If version format is unexpected, just append .1
            return version_string + '.1'
    except:
        # Fallback
        return '1.0.1'


def update_version_in_code(code, new_version, script_name=None, script_type=None, filename=None, changelog=None, author=None):
    """Update or inject standardized version header in code comments"""
    from datetime import datetime
    
    # Check if a standardized header already exists (with ==== separators)
    has_standard_header = bool(re.search(r'^//\s*=+\s*$', code, re.MULTILINE))
    
    if has_standard_header:
        # Update existing header components
        # Update Version line
        code = re.sub(
            r'//\s*Version:\s*v?[\d.]+',
            f'// Version: v{new_version}',
            code,
            flags=re.IGNORECASE
        )
        
        # Update FILENAME line if present
        if filename:
            code = re.sub(
                r'//\s*FILENAME:\s*[^\n]+',
                f'// FILENAME: {filename}',
                code,
                flags=re.IGNORECASE
            )
        
        # Update DATE line
        current_date = datetime.now().strftime('%Y-%m-%d')
        code = re.sub(
            r'//\s*DATE:\s*[^\n]+',
            f'// DATE:     {current_date}',
            code,
            flags=re.IGNORECASE
        )
        
        # Update CHANGE LOG if changelog provided
        if changelog:
            # Try to find and update CHANGE LOG section
            change_log_pattern = r'(//\s*CHANGE LOG:.*?)(\n//\s*v[\d.]+.*?)(\n//\s*(?:STRENGTHS|WEAKNESSES|=))'
            if re.search(change_log_pattern, code, re.DOTALL | re.IGNORECASE):
                # Prepend new changelog entry
                new_entry = f"\n//   v{new_version} - {changelog}"
                code = re.sub(
                    change_log_pattern,
                    rf'\1{new_entry}\2\3',
                    code,
                    flags=re.DOTALL | re.IGNORECASE
                )
    
    else:
        # No standard header exists - inject full header template
        pine_version_match = re.search(r'^(//@version=[56])\s*$', code, re.MULTILINE)
        if pine_version_match:
            # Get current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Build standardized header
            header_lines = [
                "// =============================================================================",
                f"// {script_type or 'INDICATOR'}: {script_name or 'Unknown Script'}",
                f"// FILENAME: {filename or 'unknown.pine'}",
                f"// Version: v{new_version}",
                f"// DATE:     {current_date}",
                "// =============================================================================",
                "// CHANGE LOG:",
                f"//   v{new_version} - {changelog or 'Initial versioned release'}",
                "//",
                "//   STRENGTHS: [To be documented]",
                "//   WEAKNESSES: [To be documented]",
                "// ============================================================================="
            ]
            
            # Inject after //@version=X line
            injection_point = pine_version_match.end()
            before = code[:injection_point]
            after = code[injection_point:]
            
            header_block = "\n" + "\n".join(header_lines)
            code = f"{before}{header_block}{after}"
    
    return code


if __name__ == '__main__':
    print("=" * 70)
    print("Pine Script Library API Server with Version Control")
    print("=" * 70)
    print("Server running at: http://localhost:5000")
    print("Open web interface: http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  Scripts:")
    print("   GET    /api/scripts                      - List all scripts")
    print("   GET    /api/scripts/:id                  - Get single script")
    print("   GET    /api/scripts/:id/code             - Get code (current or ?version=x)")
    print("   GET    /api/scripts/:id/review           - Review code quality")
    print("   POST   /api/scripts/:id/autofix          - Auto-fix (creates new version)")
    print("   POST   /api/scripts                      - Create new script")
    print("   PUT    /api/scripts/:id                  - Update script")
    print("   DELETE /api/scripts/:id                  - Delete script")
    print("\n  Version Control:")
    print("   GET    /api/scripts/:id/versions         - Get version history")
    print("   POST   /api/scripts/:id/versions/:v/restore - Restore version")
    print("   POST   /api/scripts/:id/save-code        - Save edited code (creates new version)")
    print("\n  Backups:")
    print("   GET    /api/backups                      - List backups")
    print("   POST   /api/backups/:file                - Restore backup")
    print("=" * 70)
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
