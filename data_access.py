from database import get_connection, release_connection

# User operations
def set_birthday(user_id, guild_id, birthday):
    """Set a user's birthday"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, guild_id, birthday)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, guild_id) 
                DO UPDATE SET birthday = EXCLUDED.birthday
            """, (user_id, guild_id, birthday))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error setting birthday: {e}")
        return False
    finally:
        release_connection(conn)

def clear_birthday(user_id, guild_id):
    """Clear a user's birthday"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM users
                WHERE user_id = %s AND guild_id = %s
            """, (user_id, guild_id))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error clearing birthday: {e}")
        return False
    finally:
        release_connection(conn)

def set_birth_year(user_id, guild_id, birth_year):
    """Set a user's birth year"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users 
                SET birth_year = %s
                WHERE user_id = %s AND guild_id = %s
            """, (birth_year, user_id, guild_id))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error setting birth year: {e}")
        return False
    finally:
        release_connection(conn)

def toggle_user_setting(user_id, guild_id, setting, value=None):
    """Toggle a user setting or set to a specific value"""
    valid_settings = ['announce_in_servers', 'receive_dms', 'share_age']
    if setting not in valid_settings:
        return False
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # If value is None, toggle the current value
            if value is None:
                cur.execute(f"""
                    UPDATE users 
                    SET {setting} = CASE WHEN {setting} = 1 THEN 0 ELSE 1 END
                    WHERE user_id = %s AND guild_id = %s
                    RETURNING {setting}
                """, (user_id, guild_id))
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else None
            # Otherwise set to the specified value
            else:
                cur.execute(f"""
                    UPDATE users 
                    SET {setting} = %s
                    WHERE user_id = %s AND guild_id = %s
                """, (value, user_id, guild_id))
                conn.commit()
                return value if cur.rowcount > 0 else None
    except Exception as e:
        conn.rollback()
        print(f"Error toggling {setting}: {e}")
        return None
    finally:
        release_connection(conn)

def get_user_birthday(user_id, guild_id):
    """Get a user's birthday information"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT birthday, birth_year, announce_in_servers, receive_dms, share_age
                FROM users
                WHERE user_id = %s AND guild_id = %s
            """, (user_id, guild_id))
            return cur.fetchone()
    except Exception as e:
        print(f"Error getting birthday: {e}")
        return None
    finally:
        release_connection(conn)

def get_birthdays_for_date(date_str):
    """Get all users with birthdays on a specific date"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, guild_id, birth_year, announce_in_servers, receive_dms, share_age
                FROM users
                WHERE birthday = %s
            """, (date_str,))
            return cur.fetchall()
    except Exception as e:
        print(f"Error getting birthdays for date: {e}")
        return []
    finally:
        release_connection(conn)

# Server settings operations
def set_server_setting(guild_id, setting, value):
    """Set a server setting"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO settings (guild_id, setting, value)
                VALUES (%s, %s, %s)
                ON CONFLICT (guild_id, setting) 
                DO UPDATE SET value = EXCLUDED.value
            """, (guild_id, setting, value))
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error setting server setting: {e}")
        return False
    finally:
        release_connection(conn)

def get_server_setting(guild_id, setting):
    """Get a server setting"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT value
                FROM settings
                WHERE guild_id = %s AND setting = %s
            """, (guild_id, setting))
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error getting server setting: {e}")
        return None
    finally:
        release_connection(conn)

def clean_up_user_data(user_id, guild_id=None):
    """Remove user data from database"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if guild_id:
                # Remove user from specific guild
                cur.execute("""
                    DELETE FROM users
                    WHERE user_id = %s AND guild_id = %s
                """, (user_id, guild_id))
            else:
                # Remove user from all guilds
                cur.execute("""
                    DELETE FROM users
                    WHERE user_id = %s
                """, (user_id,))
            conn.commit()
            return cur.rowcount
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning up user data: {e}")
        return 0
    finally:
        release_connection(conn) 