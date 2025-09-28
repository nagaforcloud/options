"""
Test Runner for Options Wheel Strategy Trading Bot
Executes all tests in the project in a structured manner
"""
import unittest
import sys
import os
import time
from datetime import datetime
import subprocess
import argparse
from pathlib import Path

# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def run_unit_tests():
    """Run unit tests"""
    print("Running unit tests...")
    
    # Find all test files in the tests directory
    test_dir = Path("tests")
    if test_dir.exists():
        loader = unittest.TestLoader()
        suite = loader.discover("tests", pattern="test_*.py")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
    else:
        print("No tests directory found, checking for test files in main directory...")
        # Look for test files in the main trading directory
        loader = unittest.TestLoader()
        suite = loader.discover(".", pattern="*test*.py")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result


def run_basic_functionality_tests():
    """Run basic functionality tests"""
    print("Running basic functionality tests...")
    
    # Import and run the basic functionality tests
    from basic_functionality_test import run_basic_tests
    result = run_basic_tests()
    
    return result


def run_smoke_tests():
    """Run smoke tests to verify basic functionality"""
    print("Running smoke tests...")
    
    # Create a simple test suite for smoke testing
    suite = unittest.TestSuite()
    
    # Add simple import tests to verify modules can be loaded
    import_tests = []
    
    try:
        import config.config
        import models.enums
        import models.models
        import utils.logging_utils
        import database.database
        import risk_management.risk_manager
        import core.strategy
        import notifications.notification_manager
        
        print("✓ All major modules imported successfully")
        smoke_test_result = unittest.TestResult()
        smoke_test_result.testsRun = 1
        return smoke_test_result
    except ImportError as e:
        print(f"✗ Smoke test failed due to import error: {e}")
        smoke_test_result = unittest.TestResult()
        smoke_test_result.testsRun = 1
        smoke_test_result.failures.append((None, str(e)))
        return smoke_test_result


def run_integration_tests():
    """Run integration tests"""
    print("Running integration tests...")
    
    # For now, we'll treat this as a subset of our basic functionality tests
    # In a full implementation, this would test interactions between components
    return run_basic_functionality_tests()


def run_performance_tests():
    """Run basic performance tests"""
    print("Running performance tests...")
    
    start_time = time.time()
    
    # Simple performance test - import core modules and measure time
    import_times = {}
    
    modules_to_test = [
        ("config.config", "Config"),
        ("models.models", "Models"),
        ("utils.logging_utils", "Logging"),
        ("database.database", "Database"),
        ("risk_management.risk_manager", "Risk"),
        ("core.strategy", "Strategy")
    ]
    
    for module_path, name in modules_to_test:
        module_start = time.time()
        __import__(module_path)
        module_end = time.time()
        import_times[name] = module_end - module_start
        print(f"  {name}: {import_times[name]:.4f}s")
    
    total_time = time.time() - start_time
    print(f"Total import time: {total_time:.4f}s")
    
    # Create a mock test result
    result = unittest.TestResult()
    result.testsRun = len(modules_to_test)
    result.performance_times = import_times
    
    return result


def generate_test_report(results, output_file="test_report.txt"):
    """Generate a test report"""
    print(f"Generating test report: {output_file}")
    
    with open(output_file, 'w') as f:
        f.write("Options Wheel Strategy Trading Bot - Test Report\n")
        f.write("=" * 60 + "\n")
        f.write(f"Test Run Date: {datetime.now()}\n\n")
        
        # Write summary
        f.write("Test Summary:\n")
        if hasattr(results.get('unit', None), 'testsRun'):
            unit = results['unit']
            f.write(f"  Unit Tests: {unit.testsRun} run, {len(unit.failures)} failures, {len(unit.errors)} errors\n")
        
        if hasattr(results.get('basic', None), 'testsRun'):
            basic = results['basic']
            f.write(f"  Basic Functionality: {basic.testsRun} run, {len(basic.failures)} failures, {len(basic.errors)} errors\n")
        
        if hasattr(results.get('smoke', None), 'testsRun'):
            smoke = results['smoke']
            f.write(f"  Smoke Tests: {smoke.testsRun} run, {len(smoke.failures)} failures, {len(smoke.errors)} errors\n")
        
        f.write(f"\nTotal execution time: {results.get('total_time', 0):.2f}s\n")
        
        # Write details for failed tests
        for test_type, result in results.items():
            if test_type not in ['total_time'] and hasattr(result, 'failures') and result.failures:
                f.write(f"\n{test_type.title()} Test Failures:\n")
                for test, traceback in result.failures:
                    f.write(f"  {test}: {traceback}\n")
            
            if test_type not in ['total_time'] and hasattr(result, 'errors') and result.errors:
                f.write(f"\n{test_type.title()} Test Errors:\n")
                for test, traceback in result.errors:
                    f.write(f"  {test}: {traceback}\n")


def main():
    """Main function to run all tests"""
    parser = argparse.ArgumentParser(description='Test Runner for Options Wheel Strategy Trading Bot')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--basic', action='store_true', help='Run basic functionality tests')
    parser.add_argument('--smoke', action='store_true', help='Run smoke tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--report', action='store_true', help='Generate test report')
    
    args = parser.parse_args()
    
    start_time = time.time()
    results = {}
    
    print("Options Wheel Strategy Trading Bot - Test Runner")
    print("=" * 60)
    print(f"Test run started at: {datetime.now()}")
    print()
    
    # Determine which tests to run
    run_all = args.all or not any([args.unit, args.basic, args.smoke, args.integration, args.performance])
    
    if run_all or args.unit:
        results['unit'] = run_unit_tests()
    
    if run_all or args.basic:
        results['basic'] = run_basic_functionality_tests()
    
    if run_all or args.smoke:
        results['smoke'] = run_smoke_tests()
    
    if run_all or args.integration:
        results['integration'] = run_integration_tests()
    
    if run_all or args.performance:
        results['performance'] = run_performance_tests()
    
    total_time = time.time() - start_time
    results['total_time'] = total_time
    
    print()
    print("=" * 60)
    print(f"Test run completed at: {datetime.now()}")
    print(f"Total execution time: {total_time:.2f}s")
    
    # Print summary
    print("\nTest Summary:")
    for test_type, result in results.items():
        if test_type == 'total_time':
            continue
        if hasattr(result, 'testsRun'):
            failures = len(getattr(result, 'failures', []))
            errors = len(getattr(result, 'errors', []))
            print(f"  {test_type.title()}: {result.testsRun} tests, {failures} failures, {errors} errors")
    
    # Generate report if requested
    if args.report:
        generate_test_report(results)
    
    # Determine exit code based on test results
    has_failures = False
    for result in results.values():
        if isinstance(result, unittest.TestResult):
            if result.failures or result.errors:
                has_failures = True
                break
    
    if has_failures:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()