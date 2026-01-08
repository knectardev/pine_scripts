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
    """Get base directory for script versions"""
    # e.g., scripts/strategies/my-strategy.pine -> scripts/strategies/my-strategy/
    path = Path(file_path)
    base_name = path.stem  # filename without extension
    version_dir = path.parent / base_name
    return version_dir


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
    
    # Create versioned file
    version_file = version_dir / f"v{initial_version}.pine"
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
        
        # Create new version file
        version_file = version_dir / f"v{new_version}.pine"
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
        
        # Create initial version file
        version_file = version_dir / f"v{initial_version}.pine"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(initial_code)
        
        # Initialize version control
        new_script['currentVersion'] = initial_version
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
            # Get current version
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
            # Get current version
            file_path = script.get('filePath')
            if not file_path:
                return jsonify({"error": "No file path specified for this script"}), 400
            
            # Read the Pine Script file
            if not os.path.exists(file_path):
                return jsonify({"error": f"Script file not found at: {file_path}"}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            current_version = script.get('currentVersion', 'current')
            script_name = f"{script.get('name', 'Unknown')} (v{current_version})"
        
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
    if '//@version=5' not in code:
        issues.append({
            'category': 'Script Structure',
            'check': 'Pine Script Version',
            'severity': 'CRITICAL',
            'message': 'Script must use //@version=5 declaration',
            'line': 1
        })
    else:
        issues.append({
            'category': 'Script Structure',
            'check': 'Pine Script Version',
            'severity': 'PASS',
            'message': 'Using Pine Script v5 ✓'
        })
    
    # ============================================================================
    # 2. NAMING CONVENTIONS CHECK
    # ============================================================================
    
    # Check for snake_case variables (should be camelCase)
    snake_case_pattern = re.compile(r'\b([a-z]+_[a-z_]+)\s*=')
    for i, line in enumerate(lines, 1):
        if '=' in line and not line.strip().startswith('//'):
            matches = snake_case_pattern.findall(line)
            for match in matches:
                # Skip if it's a constant (all caps)
                if not match.isupper():
                    issues.append({
                        'category': 'Naming Conventions',
                        'check': 'camelCase Variables',
                        'severity': 'HIGH',
                        'message': f'Variable "{match}" uses snake_case. Should use camelCase (e.g., "{to_camel_case(match)}")',
                        'line': i,
                        'code': line.strip()
                    })
    
    # Check for constants without SNAKE_CASE
    const_pattern = re.compile(r'(?:const|^)\s+(?:int|float|bool|string|color)\s+([a-z][a-zA-Z0-9]*)\s*=')
    for i, line in enumerate(lines, 1):
        if 'const' in line or (line.strip() and not line.strip().startswith('//')):
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
    
    # ============================================================================
    # 3. FORMATTING CHECKS
    # ============================================================================
    
    # Check for operators without spaces
    operator_pattern = re.compile(r'[a-zA-Z0-9_]\s*[+\-*/]=\s*[a-zA-Z0-9_]')
    for i, line in enumerate(lines, 1):
        if not line.strip().startswith('//'):
            # Check for missing spaces around operators
            if re.search(r'[a-zA-Z0-9_][+\-*/=<>!]+[a-zA-Z0-9_]', line):
                if '://' not in line and '==' not in line and '>=' not in line and '<=' not in line and '!=' not in line:
                    issues.append({
                        'category': 'Formatting',
                        'check': 'Operator Spacing',
                        'severity': 'WARNING',
                        'message': 'Missing spaces around operators. Use spaces for readability (e.g., "a = b + c")',
                        'line': i,
                        'code': line.strip()[:60]
                    })
    
    # ============================================================================
    # 4. PERFORMANCE CHECKS (ta.* function scoping)
    # ============================================================================
    
    # Check for ta.* functions inside if blocks
    ta_func_pattern = re.compile(r'ta\.\w+\(')
    in_if_block = False
    indent_level = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track if blocks
        if stripped.startswith('if '):
            in_if_block = True
            indent_level = len(line) - len(line.lstrip())
        elif in_if_block and len(line) - len(line.lstrip()) <= indent_level and stripped and not stripped.startswith('//'):
            in_if_block = False
        
        # Check for ta.* inside if blocks
        if in_if_block and ta_func_pattern.search(stripped):
            issues.append({
                'category': 'Performance',
                'check': 'ta.* Function Scoping (B8)',
                'severity': 'CRITICAL',
                'message': 'ta.* functions must be called unconditionally at global scope, not inside if blocks. This breaks internal state.',
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
            
            # Update version in code if present (keep it as current version)
            edited_code = update_version_in_code(edited_code, version_to_update)
            
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
        
        # Update version in code if present
        edited_code = update_version_in_code(edited_code, new_version)
        
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
        
        # Apply auto-fixes
        fixed_code, fixes_applied = apply_auto_fixes(code)
        
        # Increment version
        new_version = increment_version(current_version)
        
        # Update version in code
        fixed_code = update_version_in_code(fixed_code, new_version)
        
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
            'versionInfo': version_info
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
        
        # Update version in code
        final_code = update_version_in_code(final_code, new_version)
        
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
        
        # Update version in code
        fixed_code = update_version_in_code(fixed_code, new_version)
        
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
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        original_line = line
        
        # Skip comments
        if line.strip().startswith('//'):
            fixed_lines.append(line)
            i += 1
            continue
        
        # Fix 1: Add spaces around operators
        if '=' in line and not line.strip().startswith('//'):
            # Fix assignment operators without spaces
            line = re.sub(r'([a-zA-Z0-9_])=([a-zA-Z0-9_])', r'\1 = \2', line)
            line = re.sub(r'([a-zA-Z0-9_])\+=([a-zA-Z0-9_])', r'\1 += \2', line)
            line = re.sub(r'([a-zA-Z0-9_])-=([a-zA-Z0-9_])', r'\1 -= \2', line)
            line = re.sub(r'([a-zA-Z0-9_])\*=([a-zA-Z0-9_])', r'\1 *= \2', line)
            line = re.sub(r'([a-zA-Z0-9_])/=([a-zA-Z0-9_])', r'\1 /= \2', line)
            line = re.sub(r'([a-zA-Z0-9_]):=([a-zA-Z0-9_])', r'\1 := \2', line)
            
            # Fix arithmetic operators
            line = re.sub(r'([a-zA-Z0-9_])\+([a-zA-Z0-9_])', r'\1 + \2', line)
            line = re.sub(r'([a-zA-Z0-9_])-([a-zA-Z0-9_])', r'\1 - \2', line)
            line = re.sub(r'([a-zA-Z0-9_])\*([a-zA-Z0-9_])', r'\1 * \2', line)
            line = re.sub(r'([a-zA-Z0-9_])/([a-zA-Z0-9_])', r'\1 / \2', line)
            
            if line != original_line:
                fixes_applied.append(f"Line {i+1}: Added operator spacing")
        
        # Fix 2: Convert snake_case variables to camelCase (cautiously)
        # Only fix simple variable assignments, not constants
        if '=' in line and not 'const' in line and not line.strip().startswith('//'):
            # Find snake_case variable names
            snake_case_pattern = re.compile(r'\b([a-z]+_[a-z_]+)\s*=')
            matches = snake_case_pattern.findall(line)
            for match in matches:
                if not match.isupper() and 'input' not in match.lower():
                    camel_case = to_camel_case(match)
                    line = line.replace(match + ' =', camel_case + ' =')
                    fixes_applied.append(f"Line {i+1}: Converted '{match}' to '{camel_case}'")
        
        # Fix 3: Fix common ta.* scoping issues (add comment warning)
        if 'ta.' in line and line.strip().startswith('if '):
            # Add a comment warning about ta.* in if blocks
            indent = len(line) - len(line.lstrip())
            warning = ' ' * indent + '// WARNING: ta.* functions should be called at global scope\n'
            fixed_lines.append(warning + line)
            fixes_applied.append(f"Line {i+1}: Added warning about ta.* scoping")
            i += 1
            continue
        
        # Fix 4: Add //@version=5 if missing
        if i == 0 and '//@version=5' not in code[:100]:
            fixed_lines.append('//@version=5')
            fixes_applied.append("Added //@version=5 declaration")
        
        # Fix 5: Fix request.security missing parameters
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
    
    # Fix 6: Ensure proper spacing around commas in function calls
    original_code_joined = '\n'.join(lines)
    fixed_code = re.sub(r',([a-zA-Z0-9_])', r', \1', fixed_code)
    if fixed_code != original_code_joined:
        fixes_applied.append("Added spacing after commas")
    
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
        
        # Build issue summary
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


def update_version_in_code(code, new_version):
    """Update version number in code comments if present"""
    # Look for version comments and update them
    patterns = [
        (r'//\s*@version\s+v?[\d.]+', f'// @version v{new_version}'),
        (r'//\s*Version:\s*v?[\d.]+', f'// Version: v{new_version}'),
        (r'//\s*v[\d.]+', f'// v{new_version}')
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, code, re.IGNORECASE):
            code = re.sub(pattern, replacement, code, flags=re.IGNORECASE)
            break
    
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
