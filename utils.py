import re
import datetime
import pytz
from data_access import get_server_setting

def parse_birthday(birthday_str):
    """
    Parse a birthday string in either MMDD or DDMM format.
    Returns a normalized MMDD string if valid, None otherwise.
    """
    birthday_str = birthday_str.strip()
    
    # Remove any non-numeric characters
    birthday_str = re.sub(r'[^0-9]', '', birthday_str)
    
    # If they included a year, strip it out (take only first 4 digits)
    if len(birthday_str) > 4:
        birthday_str = birthday_str[:4]
    
    # If not exactly 4 digits, invalid format
    if len(birthday_str) != 4:
        return None
    
    # Try MMDD format
    try:
        month, day = int(birthday_str[:2]), int(birthday_str[2:4])
        # Check if valid date
        datetime.datetime(2000, month, day)  # Leap year to allow Feb 29
        return birthday_str  # Valid MMDD format
    except ValueError:
        pass
    
    # Try DDMM format
    try:
        day, month = int(birthday_str[:2]), int(birthday_str[2:4])
        # Check if valid date
        datetime.datetime(2000, month, day)  # Leap year to allow Feb 29
        # Return in MMDD format
        return f"{month:02d}{day:02d}"
    except ValueError:
        return None

def validate_year(year_str):
    """
    Validate a birth year string.
    Returns the year as int if valid, None otherwise.
    """
    try:
        year = int(year_str.strip())
        current_year = datetime.datetime.now().year
        
        # Check if year is within reasonable range (120 years ago to current year)
        if year > current_year or year < current_year - 120:
            return None
        
        return year
    except ValueError:
        return None

def get_current_date_mmdd(timezone=None):
    """
    Get current date in MMDD format for the specified timezone.
    If timezone is None, uses UTC.
    """
    if timezone:
        tz = pytz.timezone(timezone)
        now = datetime.datetime.now(tz)
    else:
        now = datetime.datetime.now(pytz.UTC)
    
    return now.strftime("%m%d")

def get_guild_timezone(guild_id):
    """
    Get the timezone for a guild.
    Returns the timezone string or 'UTC' if not set.
    """
    tz_str = get_server_setting(guild_id, "timezone")
    
    # Validate the timezone
    try:
        if tz_str:
            pytz.timezone(tz_str)
            return tz_str
    except pytz.exceptions.UnknownTimeZoneError:
        pass
    
    return "UTC"

def calculate_age(birth_year):
    """
    Calculate a person's age based on their birth year.
    """
    if not birth_year:
        return None
    
    current_year = datetime.datetime.now().year
    return current_year - birth_year

def is_admin(member):
    """
    Check if a member has admin privileges.
    Returns True if member has administrator permission or has a role named 'birthday'.
    """
    if member.guild_permissions.administrator:
        return True
    
    for role in member.roles:
        if role.name.lower() == "birthday":
            return True
    
    return False 