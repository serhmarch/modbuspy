"""
Test package for libmodbuspy library

This package contains comprehensive tests for all modules in the libmodbuspy library.

Test modules:
- test_mbglobal: Tests for mbglobal module (bit manipulation, enums, functions, etc.)
- test_address: Tests for Address class (construction, conversion, arithmetic, etc.)

Usage:
    # Run all tests
    python -m pytest test/
    
    # Run specific test module
    python -m pytest test/test_mbglobal.py
    
    # Run with coverage
    python -m pytest test/ --cov=libmodbuspy --cov-report=html
    
    # Run with unittest
    python -m unittest discover test/
"""

__version__ = "0.4.0"
__author__ = "serhmarch"