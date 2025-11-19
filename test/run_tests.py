"""
Test runner for libmodbuspy library

This script runs all tests for the libmodbuspy library and provides
a convenient way to execute specific test modules or all tests.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py test_mbglobal      # Run specific test module
    python run_tests.py -v                 # Run with verbose output
    python run_tests.py --coverage         # Run with coverage report
"""

import sys
import os
import unittest
import argparse

# Add the parent directory to the path to import libmodbuspy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def discover_tests(test_dir=None, pattern='test_*.py'):
    """Discover and return all tests in the test directory"""
    if test_dir is None:
        test_dir = os.path.dirname(__file__)
    
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)
    return suite


def run_specific_test(test_module):
    """Run a specific test module"""
    try:
        # Import the specific test module
        module = __import__(test_module, fromlist=[''])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        return suite
    except ImportError as e:
        print(f"Error importing test module '{test_module}': {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Run libmodbuspy tests')
    parser.add_argument('test_module', nargs='?', help='Specific test module to run')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Run tests with verbose output')
    parser.add_argument('--coverage', action='store_true',
                       help='Run tests with coverage report')
    parser.add_argument('--pattern', default='test_*.py',
                       help='Test file pattern (default: test_*.py)')
    
    args = parser.parse_args()
    
    # Set verbosity level
    verbosity = 2 if args.verbose else 1
    
    if args.coverage:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
            coverage_enabled = True
        except ImportError:
            print("Coverage package not installed. Install with: pip install coverage")
            coverage_enabled = False
    else:
        coverage_enabled = False
    
    # Create test suite
    if args.test_module:
        suite = run_specific_test(args.test_module)
        if suite is None:
            return 1
    else:
        suite = discover_tests(pattern=args.pattern)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    if coverage_enabled:
        cov.stop()
        cov.save()
        
        print("\n" + "="*50)
        print("COVERAGE REPORT")
        print("="*50)
        cov.report(show_missing=True)
        
        # Generate HTML report
        try:
            cov.html_report(directory='htmlcov')
            print(f"\nHTML coverage report generated in 'htmlcov' directory")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())