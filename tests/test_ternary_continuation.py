"""
Test Ternary Operator Line Continuation Detection and QuickFix

Tests the fix for the user-reported issue (4th-5th time):
"end of line without line continuation" error in TradingView
"""

import sys
import os

# Add parent directory to path to import server module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import perform_code_review, apply_auto_fixes


def test_ternary_continuation_detection():
    """Test that Code Review detects ternary operator without indentation"""
    
    code = """//@version=6
indicator("Test")

bool gapPoints = not na(rthOpenCurrent) and not na(rthClosePrev) ?
math.abs(rthOpenCurrent - rthClosePrev) : na
"""
    
    review = perform_code_review(code, "test_script")
    
    # Check that CRITICAL issue was detected
    critical_issues = [i for i in review['issues'] if i['severity'] == 'CRITICAL']
    ternary_issues = [i for i in critical_issues if 'Line Continuation' in i.get('check', '')]
    
    assert len(ternary_issues) > 0, "Should detect ternary continuation issue"
    
    issue = ternary_issues[0]
    assert 'indentation' in issue['message'].lower(), "Message should mention indentation"
    assert issue['line'] == 4, f"Should flag line 4 (the line with ?), got line {issue['line']}"
    
    print("[PASS] Test 1: Code Review detects ternary continuation issue")


def test_ternary_continuation_quickfix():
    """Test that QuickFix adds proper indentation"""
    
    code = """//@version=6
indicator("Test")

bool gapPoints = not na(rthOpenCurrent) and not na(rthClosePrev) ?
math.abs(rthOpenCurrent - rthClosePrev) : na
"""
    
    fixed_code, fixes = apply_auto_fixes(code)
    
    # Check that fix was applied
    ternary_fixes = [f for f in fixes if 'ternary' in f.lower() or 'continuation' in f.lower()]
    assert len(ternary_fixes) > 0, f"Should apply ternary fix. Fixes applied: {fixes}"
    
    # Check that continuation line is now indented
    lines = fixed_code.split('\n')
    continuation_line = lines[4]  # Line 5 (0-indexed as 4) - the one after the line with ?
    
    # Should start with spaces (indentation)
    assert continuation_line.startswith('    '), f"Continuation line should be indented with 4 spaces. Got: '{continuation_line}'"
    
    # Content should still be there
    assert 'math.abs' in continuation_line, "Should preserve line content"
    
    print("[PASS] Test 2: QuickFix adds proper indentation")
    print(f"   Fixed line: '{continuation_line}'")


def test_ternary_already_indented():
    """Test that already-correct code is not modified"""
    
    code = """//@version=6
indicator("Test")

bool gapPoints = not na(rthOpenCurrent) and not na(rthClosePrev) ?
    math.abs(rthOpenCurrent - rthClosePrev) : na
"""
    
    review = perform_code_review(code, "test_script")
    
    # Should NOT have operator continuation issues
    critical_issues = [i for i in review['issues'] if i['severity'] == 'CRITICAL']
    ternary_issues = [i for i in critical_issues if 'Line Continuation' in i.get('check', '')]
    
    assert len(ternary_issues) == 0, "Should NOT flag already-correct code"
    
    print("[PASS] Test 3: Already-indented code is not flagged")


def test_ternary_single_line():
    """Test that single-line ternary is not flagged"""
    
    code = """//@version=6
indicator("Test")

bool gapPoints = not na(rthOpenCurrent) and not na(rthClosePrev) ? math.abs(rthOpenCurrent - rthClosePrev) : na
"""
    
    review = perform_code_review(code, "test_script")
    
    # Should NOT have operator continuation issues
    critical_issues = [i for i in review['issues'] if i['severity'] == 'CRITICAL']
    ternary_issues = [i for i in critical_issues if 'Line Continuation' in i.get('check', '')]
    
    assert len(ternary_issues) == 0, "Should NOT flag single-line ternary"
    
    print("[PASS] Test 4: Single-line ternary is not flagged")


def test_ternary_with_comment_between():
    """Test ternary with comment line between ? and continuation"""
    
    code = """//@version=6
indicator("Test")

bool gapPoints = not na(rthOpenCurrent) and not na(rthClosePrev) ?
    // This is the true value
    math.abs(rthOpenCurrent - rthClosePrev) : na
"""
    
    review = perform_code_review(code, "test_script")
    
    # Should NOT flag (comment line is skipped, next real line is indented)
    critical_issues = [i for i in review['issues'] if i['severity'] == 'CRITICAL']
    ternary_issues = [i for i in critical_issues if 'Ternary' in i.get('check', '')]
    
    assert len(ternary_issues) == 0, "Should skip comment lines and check next real line"
    
    print("[PASS] Test 5: Comments between ? and continuation are handled")


def test_nested_ternary():
    """Test nested ternary operators"""
    
    code = """//@version=6
indicator("Test")

float result = condition1 ?
value1 : condition2 ?
value2 : defaultValue
"""
    
    review = perform_code_review(code, "test_script")
    
    # Should detect missing indentation
    critical_issues = [i for i in review['issues'] if i['severity'] == 'CRITICAL']
    ternary_issues = [i for i in critical_issues if 'Line Continuation' in i.get('check', '')]
    
    # Should flag at least the first unindented continuation
    assert len(ternary_issues) > 0, "Should detect nested ternary issues"
    
    # Apply QuickFix
    fixed_code, fixes = apply_auto_fixes(code)
    
    # Check that fixes were applied
    ternary_fixes = [f for f in fixes if 'ternary' in f.lower() or 'continuation' in f.lower()]
    assert len(ternary_fixes) > 0, "Should apply fixes to nested ternary"
    
    print("[PASS] Test 6: Nested ternary operators are handled")


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*70)
    print("TERNARY OPERATOR LINE CONTINUATION - TEST SUITE")
    print("="*70 + "\n")
    
    try:
        test_ternary_continuation_detection()
        test_ternary_continuation_quickfix()
        test_ternary_already_indented()
        test_ternary_single_line()
        test_ternary_with_comment_between()
        test_nested_ternary()
        
        print("\n" + "="*70)
        print("[SUCCESS] ALL TESTS PASSED")
        print("="*70 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
