"""
Test suite for libmodbuspy.mbglobal.Address class

Comprehensive tests for the Address class including:
- Construction from various formats
- String representations and conversions
- Integer conversions  
- Arithmetic operations
- Comparison operations
- Edge cases and error handling
"""

import unittest
import sys
import os

# Add the parent directory to the path to import libmodbuspy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.mbglobal import Address, MemoryType


class TestAddressConstruction(unittest.TestCase):
    """Test Address class construction"""

    def test_default_constructor(self):
        """Test default constructor creates invalid address"""
        addr = Address()
        self.assertFalse(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_Unknown)
        self.assertEqual(addr.offset(), 0)

    def test_constructor_with_type_and_offset(self):
        """Test constructor with memory type and offset"""
        addr = Address(MemoryType.Memory_4x, 100)
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertEqual(addr.offset(), 100)
        self.assertEqual(addr.number(), 101)

    def test_constructor_with_integer(self):
        """Test constructor with integer Modbus address"""
        # Test 400001 (Memory_4x, offset 0)
        addr = Address(400001)
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertEqual(addr.offset(), 0)
        self.assertEqual(addr.number(), 1)

        # Test 100050 (Memory_1x, offset 49)
        addr = Address(100050)
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_1x)
        self.assertEqual(addr.offset(), 49)
        self.assertEqual(addr.number(), 50)

    def test_constructor_with_string_modbus(self):
        """Test constructor with Modbus string notation"""
        # Test standard 6-digit Modbus addresses
        addr = Address("400001")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertEqual(addr.offset(), 0)

        addr = Address("300025")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_3x)
        self.assertEqual(addr.offset(), 24)

    def test_constructor_with_string_iec61131(self):
        """Test constructor with IEC 61131 string notation"""
        # Test %MW notation (holding registers)
        addr = Address("%MW0")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertEqual(addr.offset(), 0)

        addr = Address("%MW100")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertEqual(addr.offset(), 100)

        # Test %IW notation (input registers)
        addr = Address("%IW50")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_3x)
        self.assertEqual(addr.offset(), 50)

        # Test %Q notation (coils)
        addr = Address("%Q25")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_0x)
        self.assertEqual(addr.offset(), 25)

        # Test %I notation (discrete inputs)
        addr = Address("%I75")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_1x)
        self.assertEqual(addr.offset(), 75)

    def test_constructor_with_string_iec61131_hex(self):
        """Test constructor with IEC 61131 hex notation"""
        # Test %MW0000h notation
        addr = Address("%MW0000h")
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertEqual(addr.offset(), 0)

        addr = Address("%MW0064h")  # 0x64 = 100 decimal
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertEqual(addr.offset(), 100)

        addr = Address("%Q001Fh")  # 0x1F = 31 decimal
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_0x)
        self.assertEqual(addr.offset(), 31)

    def test_constructor_invalid_parameters(self):
        """Test constructor with invalid parameters"""
        # Invalid memory type
        with self.assertRaises(ValueError):
            Address(5, 0)  # Memory type 5 doesn't exist

        # Invalid offset (negative)
        with self.assertRaises(ValueError):
            Address(MemoryType.Memory_4x, -1)

        # Invalid offset (too large)
        with self.assertRaises(ValueError):
            Address(MemoryType.Memory_4x, 65536)

        # Invalid mixed parameters
        with self.assertRaises(ValueError):
            Address("invalid", 100)


class TestAddressValidation(unittest.TestCase):
    """Test Address validation and edge cases"""

    def test_invalid_integer_addresses(self):
        """Test invalid integer address handling"""
        # Number part out of range (0)
        with self.assertRaises(ValueError):
            Address(400000)
        
        # Number part out of range (too large)
        with self.assertRaises(ValueError):
            Address(465537)  # Number part would be 65537

        # Invalid memory type prefix
        with self.assertRaises(ValueError):
            Address(500001)  # Memory type 5 doesn't exist

    def test_invalid_string_addresses(self):
        """Test invalid string address handling"""
        # Invalid IEC notation prefix - raises ValueError
        with self.assertRaises(ValueError):
            Address("%XW0")

        # Invalid characters in number - creates invalid address
        with self.assertRaises(ValueError):
            Address("40000A")

        # Empty string results in integer 0, which raises ValueError
        with self.assertRaises(ValueError):
            Address("")

    def test_edge_case_addresses(self):
        """Test edge case addresses"""
        # Maximum valid addresses
        addr = Address(465536)  # Memory_4x with maximum offset
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.offset(), 65535)

        # Minimum valid addresses
        addr = Address(1)  # Memory_0x with offset 0
        self.assertTrue(addr.isvalid())
        self.assertEqual(addr.type(), MemoryType.Memory_0x)
        self.assertEqual(addr.offset(), 0)


class TestAddressStringConversion(unittest.TestCase):
    """Test Address string conversion methods"""

    def test_tostr_default_notation(self):
        """Test tostr with default (Modbus) notation"""
        addr = Address(MemoryType.Memory_4x, 0)
        self.assertEqual(addr.tostr(), "400001")
        
        addr = Address(MemoryType.Memory_3x, 99)
        self.assertEqual(addr.tostr(), "300100")

    def test_tostr_modbus_notation(self):
        """Test tostr with explicit Modbus notation"""
        addr = Address(MemoryType.Memory_1x, 24)
        result = addr.tostr(Address.Notation_Modbus)
        self.assertEqual(result, "100025")

    def test_tostr_iec61131_notation(self):
        """Test tostr with IEC 61131 notation"""
        addr = Address(MemoryType.Memory_4x, 100)
        result = addr.tostr(Address.Notation_IEC61131)
        self.assertEqual(result, "%MW100")

        addr = Address(MemoryType.Memory_0x, 25)
        result = addr.tostr(Address.Notation_IEC61131)
        self.assertEqual(result, "%Q25")

    def test_tostr_iec61131_hex_notation(self):
        """Test tostr with IEC 61131 hex notation"""
        addr = Address(MemoryType.Memory_4x, 100)
        result = addr.tostr(Address.Notation_IEC61131Hex)
        self.assertEqual(result, "%MW0064h")  # 100 = 0x64

        addr = Address(MemoryType.Memory_0x, 31)
        result = addr.tostr(Address.Notation_IEC61131Hex)
        self.assertEqual(result, "%Q001Fh")  # 31 = 0x1F

    def test_tostr_invalid_address(self):
        """Test tostr with invalid address"""
        addr = Address()  # Invalid address
        result = addr.tostr()
        self.assertEqual(result, "Invalid address")

    def test_str_and_repr(self):
        """Test __str__ and __repr__ methods"""
        addr = Address(400001)
        self.assertEqual(str(addr), "400001")
        self.assertEqual(repr(addr), "400001")


class TestAddressIntegerConversion(unittest.TestCase):
    """Test Address integer conversion methods"""

    def test_toint(self):
        """Test toint method"""
        addr = Address(MemoryType.Memory_4x, 0)
        self.assertEqual(addr.toint(), 400001)

        addr = Address(MemoryType.Memory_3x, 99)
        self.assertEqual(addr.toint(), 300100)

        addr = Address(MemoryType.Memory_1x, 24)
        self.assertEqual(addr.toint(), 100025)

        addr = Address(MemoryType.Memory_0x, 49)
        self.assertEqual(addr.toint(), 50)

    def test_int_conversion(self):
        """Test int() conversion"""
        addr = Address(400050)
        self.assertEqual(int(addr), 400050)

    def test_fromint_toint_roundtrip(self):
        """Test that fromint and toint are inverses"""
        test_values = [1, 50, 100025, 300100, 400001, 465536]
        
        for value in test_values:
            addr = Address(value)
            self.assertEqual(addr.toint(), value)


class TestAddressProperties(unittest.TestCase):
    """Test Address property methods"""

    def test_type_property(self):
        """Test type getter and setter"""
        addr = Address()
        
        # Set valid type
        addr.settype(MemoryType.Memory_4x)
        self.assertEqual(addr.type(), MemoryType.Memory_4x)
        self.assertTrue(addr.isvalid())

        # Try to set invalid type
        with self.assertRaises(ValueError):
            addr.settype(5)

    def test_offset_property(self):
        """Test offset getter and setter"""
        addr = Address(MemoryType.Memory_4x, 0)
        
        # Set valid offset
        addr.setoffset(100)
        self.assertEqual(addr.offset(), 100)
        self.assertEqual(addr.number(), 101)

        # Try to set invalid offset
        with self.assertRaises(ValueError):
            addr.setoffset(-1)
        
        with self.assertRaises(ValueError):
            addr.setoffset(65536)

    def test_number_property(self):
        """Test number getter and setter"""
        addr = Address(MemoryType.Memory_4x, 0)
        
        # number is offset + 1
        self.assertEqual(addr.number(), 1)
        
        addr.setnumber(100)
        self.assertEqual(addr.number(), 100)
        self.assertEqual(addr.offset(), 99)

        # Test edge cases
        addr.setnumber(1)
        self.assertEqual(addr.offset(), 0)

        addr.setnumber(65536)
        self.assertEqual(addr.offset(), 65535)


class TestAddressArithmetic(unittest.TestCase):
    """Test Address arithmetic operations"""

    def test_addition(self):
        """Test address addition"""
        addr = Address(400001)  # Memory_4x, offset 0
        new_addr = addr + 10
        
        self.assertEqual(new_addr.type(), MemoryType.Memory_4x)
        self.assertEqual(new_addr.offset(), 10)
        self.assertEqual(new_addr.toint(), 400011)

        # Original address should be unchanged
        self.assertEqual(addr.offset(), 0)

    def test_subtraction(self):
        """Test address subtraction"""
        addr = Address(400011)  # Memory_4x, offset 10
        new_addr = addr - 5
        
        self.assertEqual(new_addr.type(), MemoryType.Memory_4x)
        self.assertEqual(new_addr.offset(), 5)
        self.assertEqual(new_addr.toint(), 400006)

    def test_in_place_addition(self):
        """Test in-place addition"""
        addr = Address(400001)
        addr += 10
        
        self.assertEqual(addr.offset(), 10)
        self.assertEqual(addr.toint(), 400011)

    def test_in_place_subtraction(self):
        """Test in-place subtraction"""
        addr = Address(400011)
        addr -= 5
        
        self.assertEqual(addr.offset(), 5)
        self.assertEqual(addr.toint(), 400006)

    def test_arithmetic_edge_cases(self):
        """Test arithmetic with edge cases"""
        addr = Address(400001)
        
        # Addition that would cause overflow should raise exception
        with self.assertRaises(ValueError):
            addr + 65536  # Would make offset > 65535

        # Subtraction that would cause underflow should raise exception  
        with self.assertRaises(ValueError):
            addr - 1  # Would make offset < 0


class TestAddressComparison(unittest.TestCase):
    """Test Address comparison operations"""

    def test_equality(self):
        """Test address equality"""
        addr1 = Address(400001)
        addr2 = Address(400001)
        addr3 = Address(400002)
        
        self.assertEqual(addr1, addr2)
        self.assertNotEqual(addr1, addr3)

    def test_less_than(self):
        """Test address less than comparison"""
        addr1 = Address(400001)
        addr2 = Address(400002)
        addr3 = Address(300001)
        
        self.assertLess(addr1, addr2)
        self.assertLess(addr3, addr1)  # Different memory types

    def test_greater_than(self):
        """Test address greater than comparison"""
        addr1 = Address(400002)
        addr2 = Address(400001)
        addr3 = Address(300001)
        
        self.assertGreater(addr1, addr2)
        self.assertGreater(addr1, addr3)

    def test_less_equal_greater_equal(self):
        """Test <= and >= operations"""
        addr1 = Address(400001)
        addr2 = Address(400001)
        addr3 = Address(400002)
        
        self.assertLessEqual(addr1, addr2)
        self.assertLessEqual(addr1, addr3)
        self.assertGreaterEqual(addr1, addr2)
        self.assertGreaterEqual(addr3, addr1)

    def test_hash(self):
        """Test address hashing"""
        addr1 = Address(400001)
        addr2 = Address(400001)
        addr3 = Address(400002)
        
        # Equal addresses should have equal hashes
        self.assertEqual(hash(addr1), hash(addr2))
        
        # Different addresses should have different hashes (usually)
        self.assertNotEqual(hash(addr1), hash(addr3))

    def test_comparison_with_invalid_addresses(self):
        """Test comparison with invalid addresses"""
        valid_addr = Address(400001)
        invalid_addr = Address()
        
        # Comparisons should still work based on toint() values
        self.assertNotEqual(valid_addr, invalid_addr)


class TestAddressStaticMembers(unittest.TestCase):
    """Test Address static members and constants"""

    def test_memory_type_set(self):
        """Test MemoryTypeSet contains correct values"""
        expected_types = {
            MemoryType.Memory_0x,
            MemoryType.Memory_1x, 
            MemoryType.Memory_3x,
            MemoryType.Memory_4x
        }
        self.assertEqual(Address.MemoryTypeSet, expected_types)

    def test_iec61131_prefix_map(self):
        """Test IEC61131PrefixMap has correct mappings"""
        expected_map = {
            MemoryType.Memory_0x: "%Q",
            MemoryType.Memory_1x: "%I",
            MemoryType.Memory_3x: "%IW",
            MemoryType.Memory_4x: "%MW"
        }
        self.assertEqual(Address.IEC61131PrefixMap, expected_map)

    def test_notation_constants(self):
        """Test notation constants have correct values"""
        self.assertEqual(Address.Notation_Default, 0)
        self.assertEqual(Address.Notation_Modbus, 1)
        self.assertEqual(Address.Notation_IEC61131, 2)
        self.assertEqual(Address.Notation_IEC61131Hex, 3)

    def test_prefix_constants(self):
        """Test IEC 61131 prefix constants"""
        self.assertEqual(Address.sIEC61131Prefix0x, "%Q")
        self.assertEqual(Address.sIEC61131Prefix1x, "%I")
        self.assertEqual(Address.sIEC61131Prefix3x, "%IW")
        self.assertEqual(Address.sIEC61131Prefix4x, "%MW")
        self.assertEqual(Address.cIEC61131SuffixHex, 'h')


class TestAddressComplexScenarios(unittest.TestCase):
    """Test complex Address usage scenarios"""

    def test_address_range_iteration(self):
        """Test creating address ranges for iteration"""
        start_addr = Address(400001)
        addresses = []
        
        for i in range(10):
            addresses.append(start_addr + i)
        
        self.assertEqual(len(addresses), 10)
        self.assertEqual(addresses[0].toint(), 400001)
        self.assertEqual(addresses[9].toint(), 400010)

    def test_address_sorting(self):
        """Test sorting addresses"""
        addresses = [
            Address(400010),
            Address(300005),
            Address(400001),
            Address(100020)
        ]
        
        sorted_addresses = sorted(addresses)
        
        # Should be sorted by integer value
        expected_order = [100020, 300005, 400001, 400010]
        actual_order = [addr.toint() for addr in sorted_addresses]
        self.assertEqual(actual_order, expected_order)

    def test_address_in_set(self):
        """Test using addresses in sets"""
        addr_set = {
            Address(400001),
            Address(400002),
            Address(400001)  # Duplicate
        }
        
        # Should only have 2 unique addresses
        self.assertEqual(len(addr_set), 2)
        self.assertIn(Address(400001), addr_set)
        self.assertNotIn(Address(400003), addr_set)

    def test_mixed_memory_types(self):
        """Test operations with different memory types"""
        coil_addr = Address(50)      # Memory_0x
        input_addr = Address(100050) # Memory_1x  
        holding_addr = Address(400050) # Memory_4x
        
        # All should be valid but different types
        self.assertTrue(all(addr.isvalid() for addr in [coil_addr, input_addr, holding_addr]))
        self.assertEqual(coil_addr.type(), MemoryType.Memory_0x)
        self.assertEqual(input_addr.type(), MemoryType.Memory_1x)
        self.assertEqual(holding_addr.type(), MemoryType.Memory_4x)

        # But all have same offset
        self.assertEqual(coil_addr.offset(), 49)
        self.assertEqual(input_addr.offset(), 49)
        self.assertEqual(holding_addr.offset(), 49)


if __name__ == '__main__':
    unittest.main(verbosity=2)