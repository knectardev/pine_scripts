"""
Test Type Mismatch Detection and QuickFix
Tests the new type mismatch detection and automatic fixing in server.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import perform_code_review, apply_auto_fixes

def test_ta_change_type_mismatch():
    """Test ta.change() returns int, not bool"""
    code = """
//@version=6
indicator("Test", overlay=true)

bool timeChange = ta.change(time)
"""
    
    print("=" * 80)
    print("TEST 1: ta.change() Type Mismatch Detection")
    print("=" * 80)
    
    # Check if code review detects the issue
    review_result = perform_code_review(code, "test")
    issues = review_result.get('issues', [])
    type_mismatch_issues = [i for i in issues if i.get('category') == 'Type Mismatch']
    
    print(f"\n[OK] Code Review found {len(type_mismatch_issues)} type mismatch issue(s)")
    if type_mismatch_issues:
        for issue in type_mismatch_issues:
            print(f"  - Line {issue['line']}: {issue['message']}")
    
    # Apply fixes
    fixed_code, fixes_applied = apply_auto_fixes(code)
    
    print(f"\n[OK] QuickFix applied {len(fixes_applied)} fix(es)")
    type_fixes = [f for f in fixes_applied if 'type' in f.lower()]
    for fix in type_fixes:
        print(f"  - {fix}")
    
    # Verify the fix
    if 'int timeChange = ta.change(time)' in fixed_code:
        print("\n[PASS] Type changed from bool to int")
    else:
        print("\n[FAIL] Type not changed correctly")
        print("Fixed code:")
        print(fixed_code)


def test_na_function_type_mismatch():
    """Test na() returns bool, not int/float"""
    code = """
//@version=6
indicator("Test", overlay=true)

float isPivotHighNull = na(high)
int isPivotLowNull = na(low)
"""
    
    print("\n" + "=" * 80)
    print("TEST 2: na() Type Mismatch Detection")
    print("=" * 80)
    
    # Check if code review detects the issue
    review_result = perform_code_review(code, "test")
    issues = review_result.get('issues', [])
    type_mismatch_issues = [i for i in issues if i.get('category') == 'Type Mismatch']
    
    print(f"\n[OK] Code Review found {len(type_mismatch_issues)} type mismatch issue(s)")
    if type_mismatch_issues:
        for issue in type_mismatch_issues:
            print(f"  - Line {issue['line']}: {issue['message']}")
    
    # Apply fixes
    fixed_code, fixes_applied = apply_auto_fixes(code)
    
    print(f"\n[OK] QuickFix applied {len(fixes_applied)} fix(es)")
    type_fixes = [f for f in fixes_applied if 'type' in f.lower()]
    for fix in type_fixes:
        print(f"  - {fix}")
    
    # Verify the fix
    if 'bool isPivotHighNull = na(high)' in fixed_code and 'bool isPivotLowNull = na(low)' in fixed_code:
        print("\n[PASS] Types changed from int/float to bool")
    else:
        print("\n[FAIL] Types not changed correctly")
        print("Fixed code:")
        print(fixed_code)


def test_crossover_type_mismatch():
    """Test ta.crossover() returns bool, not int/float"""
    code = """
//@version=6
indicator("Test", overlay=true)

int cross = ta.crossover(close, open)
float crossUnder = ta.crossunder(close, open)
"""
    
    print("\n" + "=" * 80)
    print("TEST 3: ta.crossover()/ta.crossunder() Type Mismatch Detection")
    print("=" * 80)
    
    # Check if code review detects the issue
    review_result = perform_code_review(code, "test")
    issues = review_result.get('issues', [])
    type_mismatch_issues = [i for i in issues if i.get('category') == 'Type Mismatch']
    
    print(f"\n[OK] Code Review found {len(type_mismatch_issues)} type mismatch issue(s)")
    if type_mismatch_issues:
        for issue in type_mismatch_issues:
            print(f"  - Line {issue['line']}: {issue['message']}")
    
    # Apply fixes
    fixed_code, fixes_applied = apply_auto_fixes(code)
    
    print(f"\n[OK] QuickFix applied {len(fixes_applied)} fix(es)")
    type_fixes = [f for f in fixes_applied if 'type' in f.lower()]
    for fix in type_fixes:
        print(f"  - {fix}")
    
    # Verify the fix
    if 'bool cross = ta.crossover(close, open)' in fixed_code and 'bool crossUnder = ta.crossunder(close, open)' in fixed_code:
        print("\n[PASS] Types changed from int/float to bool")
    else:
        print("\n[FAIL] Types not changed correctly")
        print("Fixed code:")
        print(fixed_code)


def test_pivothigh_type_mismatch():
    """Test ta.pivothigh() returns float, not bool"""
    code = """
//@version=6
indicator("Test", overlay=true)

bool pivotHigh = ta.pivothigh(high, 5, 5)
const bool pivotLow = ta.pivotlow(low, 5, 5)
"""
    
    print("\n" + "=" * 80)
    print("TEST 4: ta.pivothigh()/ta.pivotlow() Type Mismatch Detection")
    print("=" * 80)
    
    # Check if code review detects the issue
    review_result = perform_code_review(code, "test")
    issues = review_result.get('issues', [])
    type_mismatch_issues = [i for i in issues if i.get('category') == 'Type Mismatch']
    
    print(f"\n[OK] Code Review found {len(type_mismatch_issues)} type mismatch issue(s)")
    if type_mismatch_issues:
        for issue in type_mismatch_issues:
            print(f"  - Line {issue['line']}: {issue['message']}")
    
    # Apply fixes
    fixed_code, fixes_applied = apply_auto_fixes(code)
    
    print(f"\n[OK] QuickFix applied {len(fixes_applied)} fix(es)")
    type_fixes = [f for f in fixes_applied if 'type' in f.lower()]
    for fix in type_fixes:
        print(f"  - {fix}")
    
    # Verify the fix
    if 'float pivotHigh = ta.pivothigh(high, 5, 5)' in fixed_code and 'const float pivotLow = ta.pivotlow(low, 5, 5)' in fixed_code:
        print("\n[PASS] Types changed from bool to float (including const)")
    else:
        print("\n[FAIL] Types not changed correctly")
        print("Fixed code:")
        print(fixed_code)


def test_barssince_type_mismatch():
    """Test ta.barssince() returns int, not bool"""
    code = """
//@version=6
indicator("Test", overlay=true)

bool barsSince = ta.barssince(close > open)
"""
    
    print("\n" + "=" * 80)
    print("TEST 5: ta.barssince() Type Mismatch Detection")
    print("=" * 80)
    
    # Check if code review detects the issue
    review_result = perform_code_review(code, "test")
    issues = review_result.get('issues', [])
    type_mismatch_issues = [i for i in issues if i.get('category') == 'Type Mismatch']
    
    print(f"\n[OK] Code Review found {len(type_mismatch_issues)} type mismatch issue(s)")
    if type_mismatch_issues:
        for issue in type_mismatch_issues:
            print(f"  - Line {issue['line']}: {issue['message']}")
    
    # Apply fixes
    fixed_code, fixes_applied = apply_auto_fixes(code)
    
    print(f"\n[OK] QuickFix applied {len(fixes_applied)} fix(es)")
    type_fixes = [f for f in fixes_applied if 'type' in f.lower()]
    for fix in type_fixes:
        print(f"  - {fix}")
    
    # Verify the fix
    if 'int barsSince = ta.barssince(close > open)' in fixed_code:
        print("\n[PASS] Type changed from bool to int")
    else:
        print("\n[FAIL] Type not changed correctly")
        print("Fixed code:")
        print(fixed_code)


def test_user_reported_issue():
    """Test the exact issue reported by the user"""
    code = """
//@version=6
indicator("RSI Divergence Detector", overlay=true) 

bool timeChange = ta.change(time)
bool naPivotHighPrice = na(pivotHighPrice)
bool naPivotLowPrice = na(pivotLowPrice)
"""
    
    print("\n" + "=" * 80)
    print("TEST 6: User Reported Issue - Multiple Type Mismatches")
    print("=" * 80)
    
    # Check if code review detects the issue
    review_result = perform_code_review(code, "test")
    issues = review_result.get('issues', [])
    type_mismatch_issues = [i for i in issues if i.get('category') == 'Type Mismatch']
    
    print(f"\n[OK] Code Review found {len(type_mismatch_issues)} type mismatch issue(s)")
    if type_mismatch_issues:
        for issue in type_mismatch_issues:
            print(f"  - Line {issue['line']}: {issue['message']}")
    
    # Apply fixes
    fixed_code, fixes_applied = apply_auto_fixes(code)
    
    print(f"\n[OK] QuickFix applied {len(fixes_applied)} fix(es)")
    type_fixes = [f for f in fixes_applied if 'type' in f.lower()]
    for fix in type_fixes:
        print(f"  - {fix}")
    
    # Verify the fixes
    checks = [
        ('int timeChange = ta.change(time)', 'timeChange type changed to int'),
        ('bool naPivotHighPrice = na(pivotHighPrice)', 'naPivotHighPrice kept as bool'),
        ('bool naPivotLowPrice = na(pivotLowPrice)', 'naPivotLowPrice kept as bool')
    ]
    
    all_pass = True
    for check_str, check_desc in checks:
        if check_str in fixed_code:
            print(f"  [OK] {check_desc}")
        else:
            print(f"  [FAIL] {check_desc}")
            all_pass = False
    
    if all_pass:
        print("\n[PASS] All type mismatches fixed correctly")
    else:
        print("\n[FAIL] Some types not fixed correctly")
        print("\nFixed code:")
        print(fixed_code)


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("TYPE MISMATCH DETECTION & AUTO-FIX TEST SUITE")
    print("=" * 80)
    
    test_ta_change_type_mismatch()
    test_na_function_type_mismatch()
    test_crossover_type_mismatch()
    test_pivothigh_type_mismatch()
    test_barssince_type_mismatch()
    test_user_reported_issue()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
