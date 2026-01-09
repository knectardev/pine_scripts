"""
Diagnostic tool - paste your script lines 95-155 to see what's happening with the if block tracking
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# INSTRUCTIONS: Replace this with lines 95-155 from your actual script
YOUR_CODE_HERE = """
PASTE YOUR CODE FROM LINES 95-155 HERE
"""

if "PASTE YOUR CODE" in YOUR_CODE_HERE:
    print("=" * 80)
    print("PLEASE PASTE YOUR ACTUAL CODE (lines 95-155) into this file at line 16")
    print("Then run: python diagnose_line_106.py")
    print("=" * 80)
    sys.exit(0)

# Simulate the detection logic with debug output
lines = YOUR_CODE_HERE.split('\n')
if_block_stack = []
ta_func_pattern = re.compile(r'ta\.\w+\(')

print("=" * 80)
print("IF BLOCK STACK TRACKING DEBUG")
print("=" * 80)

for i, line in enumerate(lines, 95):  # Start at line 95
    stripped = line.strip()
    
    if not stripped or stripped.startswith('//'):
        continue
    
    current_indent = len(line) - len(line.lstrip())
    
    # Show stack before processing
    stack_info = f"[Stack: {len(if_block_stack)} blocks]"
    if if_block_stack:
        stack_info += f" top=(indent={if_block_stack[-1][0]}, line={if_block_stack[-1][1]})"
    
    # Pop logic
    popped = []
    while if_block_stack and current_indent <= if_block_stack[-1][0]:
        popped_item = if_block_stack.pop()
        popped.append(popped_item[1])
    
    if popped:
        print(f"Line {i} (indent={current_indent}): POP {len(popped)} blocks {popped}")
    
    # Track if/for/while
    if re.match(r'^(if|for|while)\s+', stripped):
        if_block_stack.append((current_indent, i, current_indent + 4))
        print(f"Line {i} (indent={current_indent}): PUSH if/for/while → Stack depth: {len(if_block_stack)}")
        print(f"       Code: {stripped[:60]}")
    
    # Check for ta.*
    if len(if_block_stack) > 0 and ta_func_pattern.search(stripped):
        if_line = if_block_stack[-1][1]
        print(f"Line {i} (indent={current_indent}): ⚠️  ta.* FLAGGED (if block from line {if_line})")
        print(f"       Code: {stripped[:60]}")
    elif ta_func_pattern.search(stripped):
        print(f"Line {i} (indent={current_indent}): ✓ ta.* at global scope (OK)")
        print(f"       Code: {stripped[:60]}")

print("\n" + "=" * 80)
print(f"Final stack depth: {len(if_block_stack)}")
if if_block_stack:
    print("⚠️  WARNING: Stack not empty! Unclosed if blocks from lines:")
    for indent, line_num, expected in if_block_stack:
        print(f"   - Line {line_num} (indent={indent})")
