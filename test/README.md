# ModbusPy Test Framework

Professional test framework for the `libmodbuspy` library with comprehensive testing
capabilities, coverage analysis, and flexible execution options.

## 📋 Test Framework Structure

```
test/
├── README.md              # Test framework documentation
├── __init__.py            # Test package initialization and utilities
├── run_tests.py           # Advanced test runner with coverage support
├── test_mbglobal.py       # Core module functionality tests
└── test_address.py        # Address class comprehensive tests
```

## 🎯 Framework Features

### **Advanced Test Runner** (`run_tests.py`)
Custom test runner with enhanced capabilities:

- **Flexible Test Discovery**: Automatic and manual test selection
- **Coverage Integration**: Built-in code coverage analysis
- **Multiple Output Formats**: Console, HTML, and XML reports
- **Selective Execution**: Run specific modules, classes, or methods
- **Verbose Reporting**: Detailed test execution information

### **Comprehensive Test Suite**
- **Unit Tests**: Individual function and method testing
- **Integration Tests**: Component interaction validation
- **Edge Case Testing**: Boundary conditions and error handling
- **Performance Validation**: Algorithm correctness verification
- **Type Safety Testing**: Input validation and type checking

### **Coverage Analysis**
- **Line Coverage**: Track executed code lines
- **Function Coverage**: Ensure all functions are tested
- **Branch Coverage**: Validate all code paths
- **HTML Reports**: Visual coverage analysis
- **Missing Line Detection**: Identify untested code

## 🚀 Using the Test Framework

### **Quick Start**
```bash
# Run all tests with the custom runner
python test/run_tests.py

# Run with verbose output
python test/run_tests.py -v

# Run with coverage analysis
python test/run_tests.py --coverage
```

### **Test Execution Methods**

#### **Method 1: Custom Test Runner** (Recommended)
```bash
# Basic usage
python test/run_tests.py                    # Run all tests
python test/run_tests.py -v                 # Verbose output
python test/run_tests.py --coverage         # With coverage

# Selective testing
python test/run_tests.py test_mbglobal      # Specific module
python test/run_tests.py test_address       # Specific module
python test/run_tests.py --pattern "test_mb*"  # Pattern matching
```

**Features:**
- ✅ Built-in coverage analysis
- ✅ HTML report generation  
- ✅ Selective test execution
- ✅ Error handling and reporting
- ✅ Cross-platform compatibility

#### **Method 2: Standard unittest**
```bash
# Discover and run all tests
python -m unittest discover test/ -v

# Run specific test modules
python -m unittest test.test_mbglobal -v
python -m unittest test.test_address -v

# Run specific test classes
python -m unittest test.test_mbglobal.TestBitManipulation -v

# Run specific test methods
python -m unittest test.test_mbglobal.TestBitManipulation.test_getBit_basic -v
```

The `python -m unittest discover test/` command:
- No entry point needed - uses automatic discovery
- Finds test files by pattern matching (`test_*.py`)
- Imports modules and scans for `TestCase` classes
- Executes test methods starting with `test_` 
- ` test/__init__.py` is for package structure, not entry point

#### **Method 3: pytest** (Advanced)
```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest test/

# With coverage
pytest test/ --cov=libmodbuspy --cov-report=html --cov-report=term

# Specific tests
pytest test/test_mbglobal.py::TestBitManipulation::test_getBit_basic -v

# Parallel execution
pytest test/ -n auto  # Requires pytest-xdist
```

## 📊 Coverage Analysis

### **Built-in Coverage (Custom Runner)**
```bash
# Run tests with coverage
python test/run_tests.py --coverage

# Output includes:
# - Console coverage report
# - HTML report in htmlcov/
# - Missing line identification
# - Function coverage statistics
```

**Sample Output:**
```
==========================================
COVERAGE REPORT
==========================================
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
libmodbuspy/mbglobal.py      425     12    97%   45-47, 123, 234-236
libmodbuspy/address.py       156      3    98%   89, 145, 203
-----------------------------------------------------
TOTAL                     581     15    97%

HTML coverage report generated in 'htmlcov' directory
```

### **External Coverage Tools**
```bash
# Using coverage.py directly
pip install coverage
coverage run -m unittest discover test/
coverage report -m
coverage html

# Using pytest-cov
pip install pytest-cov
pytest test/ --cov=libmodbuspy --cov-report=html
```

## 🛠️ Framework Capabilities

### **Test Discovery and Execution**
```python
# The framework automatically discovers:
# - Files matching: test_*.py
# - Classes inheriting from: unittest.TestCase  
# - Methods starting with: test_*

# Example test structure:
class TestMyFeature(unittest.TestCase):
    def test_basic_functionality(self):
        # Test implementation
        pass
    
    def test_edge_cases(self):
        # Edge case testing
        pass
```

### **Mock Integration**
```python
# Framework supports mocking for external dependencies
from unittest.mock import patch, MagicMock

class TestTimerFunctions(unittest.TestCase):
    @patch('time.sleep')
    def test_msleep(self, mock_sleep):
        msleep(100)
        mock_sleep.assert_called_once_with(0.1)
```

### **Parameterized Testing**
```python
# Test multiple scenarios with different data
class TestAddressFormats(unittest.TestCase):
    def test_multiple_address_formats(self):
        test_cases = [
            ("400001", MemoryType.Memory_4x, 0),
            ("300100", MemoryType.Memory_3x, 99),
            ("%MW50", MemoryType.Memory_4x, 50),
        ]
        
        for addr_str, expected_type, expected_offset in test_cases:
            with self.subTest(addr=addr_str):
                addr = Address(addr_str)
                self.assertEqual(addr.type(), expected_type)
                self.assertEqual(addr.offset(), expected_offset)
```

### **Error Testing**
```python
# Framework validates error handling
class TestValidation(unittest.TestCase):
    def test_invalid_input_handling(self):
        with self.assertRaises(ValueError):
            Address(999999)  # Invalid address
        
        with self.assertRaisesRegex(ValueError, "Invalid memory type"):
            Address(5, 0)  # Invalid memory type
```

## 🎯 Test Categories

### **Unit Tests**
- **Function Testing**: Individual function validation
- **Method Testing**: Class method behavior verification
- **Property Testing**: Getter/setter validation
- **Operator Testing**: Mathematical and comparison operations

### **Integration Tests**
- **Component Interaction**: Module-to-module communication
- **Data Flow Testing**: End-to-end data processing
- **Protocol Compliance**: Modbus standard adherence
- **Format Compatibility**: Multiple input format support

### **Edge Case Tests**
- **Boundary Values**: Maximum/minimum input testing
- **Invalid Inputs**: Error condition validation
- **Resource Limits**: Memory and performance boundaries
- **Type Safety**: Input type validation

### **Performance Tests**
- **Algorithm Speed**: Checksum calculation performance
- **Memory Usage**: Efficient data structure usage
- **Scalability**: Large dataset handling
- **Optimization**: Code efficiency validation

## 📈 Test Metrics and Reporting

### **Coverage Metrics**
- **Line Coverage**: Percentage of executed code lines
- **Function Coverage**: Percentage of called functions
- **Branch Coverage**: Percentage of executed code paths
- **Statement Coverage**: Individual statement execution

### **Report Formats**
```bash
# Console Report
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
libmodbuspy/mbglobal.py      425     12    97%   45-47, 123

# HTML Report (Interactive)
# Generated in htmlcov/index.html
# - Visual line-by-line coverage
# - Missing line highlighting
# - Interactive navigation

# XML Report (CI/CD Integration)
coverage xml  # Generates coverage.xml for Jenkins, etc.
```

### **Quality Gates**
```python
# Framework can enforce minimum coverage thresholds
if coverage_percentage < 95:
    print("❌ Coverage below threshold!")
    sys.exit(1)
else:
    print("✅ Coverage meets quality standards!")
```

## 🔧 Extending the Framework

### **Adding New Test Modules**
```bash
# Create new test file
touch test/test_new_module.py

# Follow naming convention: test_<module_name>.py
# Framework will automatically discover new tests
```

### **Custom Test Utilities**
```python
# Add shared utilities to test/__init__.py
def create_test_data():
    """Helper function for test data creation"""
    return {
        'addresses': [Address(400001), Address(300100)],
        'data': bytearray([0x12, 0x34, 0x56, 0x78])
    }

# Use in tests:
from test import create_test_data

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.test_data = create_test_data()
```

### **Custom Assertions**
```python
# Add domain-specific assertions
class ModbusTestCase(unittest.TestCase):
    def assertAddressEqual(self, addr1, addr2):
        """Custom assertion for address comparison"""
        self.assertEqual(addr1.type(), addr2.type())
        self.assertEqual(addr1.offset(), addr2.offset())
    
    def assertValidCRC(self, data, expected_crc):
        """Custom assertion for CRC validation"""
        calculated_crc = crc16(data)
        self.assertEqual(calculated_crc, expected_crc)
```

## 🐛 Debugging and Troubleshooting

### **Debug Mode**
```bash
# Run with maximum verbosity
python test/run_tests.py -v

# Debug specific test
python -m unittest test.test_mbglobal.TestBitManipulation.test_getBit_basic -v
```

### **Common Issues**
```python
# Import path issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock not working
from unittest.mock import patch
# Ensure correct import path in patch decorator

# Coverage not including module
# Verify module is imported during test execution
```

### **Test Output Analysis**
```bash
# Capture test output
python test/run_tests.py 2>&1 | tee test_output.log

# Filter failures
python test/run_tests.py 2>&1 | grep -E "(FAIL|ERROR)"
```

## 🔄 Continuous Integration

### **GitHub Actions Integration**
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, '3.10', '3.11']
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v3
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install coverage
      - name: Run tests with coverage
        run: python test/run_tests.py --coverage
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

### **Local Pre-commit Hook**
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Running test suite..."
python test/run_tests.py --coverage
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Commit aborted."
    exit 1
fi
echo "✅ All tests passed!"
```

## 📚 Best Practices

### **Test Organization**
- **One test file per module**: `test_<module>.py`
- **Descriptive test names**: `test_<function>_<scenario>`
- **Logical test grouping**: Related tests in same class
- **Setup and teardown**: Use `setUp()` and `tearDown()` methods

### **Test Quality**
- **Independent tests**: No dependencies between tests
- **Deterministic results**: Same input produces same output
- **Comprehensive coverage**: Test normal and edge cases
- **Clear assertions**: Meaningful error messages

### **Performance**
- **Fast execution**: Keep tests lightweight
- **Parallel safe**: No shared state between tests
- **Resource cleanup**: Proper cleanup in tearDown
- **Mock external dependencies**: Avoid network/file I/O

---

**The ModbusPy test framework provides a robust foundation for ensuring code quality and reliability.
Use it to validate your libmodbuspy implementations with confidence!** 🧪✨