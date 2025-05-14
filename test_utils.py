import unittest
import sys
import os
from datetime import datetime, timedelta
import pytz
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from utils import parse_birthday, validate_year, calculate_age, is_admin

class TestUtils(unittest.TestCase):
    
    def test_parse_birthday_mmdd(self):
        """Test parsing birthday in MMDD format"""
        self.assertEqual(parse_birthday("0101"), "0101")  # January 1
        self.assertEqual(parse_birthday("1225"), "1225")  # December 25
        self.assertEqual(parse_birthday("01/01"), "0101")  # With separator
        self.assertEqual(parse_birthday("12-25"), "1225")  # With separator
        
    def test_parse_birthday_ddmm(self):
        """Test parsing birthday in DDMM format"""
        # Day first format that's valid as MMDD too
        self.assertEqual(parse_birthday("0501"), "0501")  # May 1 or January 5
        
        # Day first format that's invalid as MMDD
        self.assertEqual(parse_birthday("3101"), "0131")  # January 31
        
    def test_parse_birthday_with_year(self):
        """Test parsing birthday with year"""
        self.assertEqual(parse_birthday("01011990"), "0101")  # January 1, 1990
        self.assertEqual(parse_birthday("12252000"), "1225")  # December 25, 2000
        
    def test_parse_birthday_invalid(self):
        """Test parsing invalid birthday formats"""
        self.assertIsNone(parse_birthday("0000"))  # Invalid month and day
        self.assertIsNone(parse_birthday("1332"))  # Invalid month
        self.assertIsNone(parse_birthday("0232"))  # Invalid day for February
        self.assertIsNone(parse_birthday("abcd"))  # Non-numeric
        self.assertIsNone(parse_birthday("123"))   # Too short
        
    def test_validate_year(self):
        """Test validating birth year"""
        current_year = datetime.now().year
        
        # Valid years
        self.assertEqual(validate_year(str(current_year)), current_year)
        self.assertEqual(validate_year(str(current_year - 50)), current_year - 50)
        
        # Invalid years
        self.assertIsNone(validate_year(str(current_year + 1)))  # Future
        self.assertIsNone(validate_year(str(current_year - 121)))  # Too old
        self.assertIsNone(validate_year("abc"))  # Non-numeric
        
    def test_calculate_age(self):
        """Test age calculation"""
        current_year = datetime.now().year
        
        self.assertEqual(calculate_age(current_year - 20), 20)
        self.assertEqual(calculate_age(current_year), 0)
        self.assertIsNone(calculate_age(None))
        
    def test_is_admin(self):
        """Test admin permission check"""
        # Mock member with admin permissions
        admin_member = MagicMock()
        admin_member.guild_permissions.administrator = True
        admin_member.roles = []
        
        # Mock member with birthday role
        birthday_role = MagicMock()
        birthday_role.name = "birthday"
        birthday_member = MagicMock()
        birthday_member.guild_permissions.administrator = False
        birthday_member.roles = [birthday_role]
        
        # Mock regular member
        regular_role = MagicMock()
        regular_role.name = "regular"
        regular_member = MagicMock()
        regular_member.guild_permissions.administrator = False
        regular_member.roles = [regular_role]
        
        # Test admin permissions
        self.assertTrue(is_admin(admin_member))
        self.assertTrue(is_admin(birthday_member))
        self.assertFalse(is_admin(regular_member))
        
if __name__ == '__main__':
    unittest.main() 