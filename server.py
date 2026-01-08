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


@app.route('/api/scripts/<script_id>/code', methods=['GET'])
def get_script_code(script_id):
    """Get Pine Script source code for a script"""
    try:
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Get file path
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
            "filePath": file_path,
            "code": code
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scripts/<script_id>/review', methods=['GET'])
def review_script_code(script_id):
    """Review Pine Script code against standards and best practices"""
    try:
        # Load scripts metadata
        data = load_scripts()
        script = next((s for s in data['scripts'] if s['id'] == script_id), None)
        
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # Get file path
        file_path = script.get('filePath')
        if not file_path:
            return jsonify({"error": "No file path specified for this script"}), 400
        
        # Read the Pine Script file
        if not os.path.exists(file_path):
            return jsonify({"error": f"Script file not found at: {file_path}"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Perform code review
        review_results = perform_code_review(code, script.get('name', 'Unknown'))
        
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
    var_pattern = re.compile(r'var\s+\w+\s+(\w+)\s*=')
    vars_found = []
    for i, line in enumerate(lines, 1):
        matches = var_pattern.findall(line)
        for var_name in matches:
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


if __name__ == '__main__':
    print("=" * 60)
    print("Pine Script Library API Server")
    print("=" * 60)
    print("Server running at: http://localhost:5000")
    print("Open web interface: http://localhost:5000")
    print("API Endpoints:")
    print("   GET    /api/scripts             - List all scripts")
    print("   GET    /api/scripts/:id         - Get single script")
    print("   GET    /api/scripts/:id/code    - Get script source code")
    print("   GET    /api/scripts/:id/review  - Review script code quality")
    print("   POST   /api/scripts             - Create new script")
    print("   PUT    /api/scripts/:id         - Update script")
    print("   DELETE /api/scripts/:id         - Delete script")
    print("   GET    /api/backups             - List backups")
    print("   POST   /api/backups/:file       - Restore backup")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
