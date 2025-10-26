import sqlite3
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._create_table_if_not_exists()

    def _get_db_connection(self):
        """Helper to get a new database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row # Allows accessing columns by name
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error getting database connection: {e}")
            raise

    def _create_table_if_not_exists(self):
        """
        Creates the properties table if it does not exist.
        Also handles adding new columns for schema evolution.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Create table if it doesn't exist with all new columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL UNIQUE,
                    original_file_path TEXT,
                    extraction_date TEXT,
                    raw_text_preview TEXT,
                    original_extracted_data_json TEXT,   -- New: Stores data directly from PDF
                    user_input_data_json TEXT,           -- Renamed/New: Stores user's current/saved inputs
                    calculated_financials_json TEXT
                )
            ''')
            conn.commit()

            # --- Simple Schema Migration for existing databases ---
            # Check and add 'original_extracted_data_json' if it doesn't exist
            cursor.execute("PRAGMA table_info(properties)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'original_extracted_data_json' not in columns:
                cursor.execute("ALTER TABLE properties ADD COLUMN original_extracted_data_json TEXT")
                conn.commit()
                logger.info("Added 'original_extracted_data_json' column to 'properties' table.")

            # Check and add 'user_input_data_json' if it doesn't exist
            # Note: If you had 'extracted_data_json' previously, you might want to
            # copy its content to 'user_input_data_json' in a more complex migration.
            # For simplicity, we're assuming 'user_input_data_json' is new.
            if 'user_input_data_json' not in columns:
                cursor.execute("ALTER TABLE properties ADD COLUMN user_input_data_json TEXT")
                conn.commit()
                logger.info("Added 'user_input_data_json' column to 'properties' table.")
            # --- End Migration ---

            logger.info("Database table 'properties' ensured.")
        except sqlite3.Error as e:
            logger.error(f"Error creating table or migrating schema: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def insert_property(self, file_name, original_file_path, raw_text_preview, original_extracted_data, user_input_data, calculated_financials):
        """
        Inserts a new property record into the database.
        Includes both original extracted data and initial user input data.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            extraction_date = datetime.now().isoformat()
            original_extracted_data_json = json.dumps(original_extracted_data)
            user_input_data_json = json.dumps(user_input_data)
            calculated_financials_json = json.dumps(calculated_financials)

            cursor.execute('''
                INSERT INTO properties (file_name, original_file_path, extraction_date, raw_text_preview, original_extracted_data_json, user_input_data_json, calculated_financials_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (file_name, original_file_path, extraction_date, raw_text_preview, original_extracted_data_json, user_input_data_json, calculated_financials_json))
            conn.commit()
            new_id = cursor.lastrowid
            logger.info(f"Inserted new property: {file_name} with ID {new_id}")
            return new_id
        except sqlite3.IntegrityError:
            logger.warning(f"Property with file name '{file_name}' already exists. Skipping insertion.")
            return None
        except sqlite3.Error as e:
            logger.error(f"Error inserting property {file_name}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_property(self, property_id, file_name, original_file_path, raw_text_preview, user_input_data, calculated_financials):
        """
        Updates an existing property record in the database.
        Only updates user_input_data_json and calculated_financials_json.
        original_extracted_data_json is NOT updated here.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            user_input_data_json = json.dumps(user_input_data)
            calculated_financials_json = json.dumps(calculated_financials)

            cursor.execute('''
                UPDATE properties
                SET file_name = ?, original_file_path = ?, raw_text_preview = ?, user_input_data_json = ?, calculated_financials_json = ?
                WHERE id = ?
            ''', (file_name, original_file_path, raw_text_preview, user_input_data_json, calculated_financials_json, property_id))
            conn.commit()
            logger.info(f"Updated property with ID: {property_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating property {property_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_properties_summary(self):
        """
        Fetches a summary of all properties (id, file_name, extraction_date).
        A new connection is opened and closed within this method.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, file_name, extraction_date FROM properties ORDER BY extraction_date DESC')
            rows = cursor.fetchall()
            return [{'id': row['id'], 'file_name': row['file_name'], 'extraction_date': row['extraction_date']} for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error fetching all properties summary: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_all_properties(self):
        """
        Fetches all properties with as much detail as stored in the DB.
        Returns a list of dicts keyed by column names.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, file_name, original_file_path, extraction_date, raw_text_preview, original_extracted_data_json, user_input_data_json, calculated_financials_json FROM properties ORDER BY extraction_date DESC')
            rows = cursor.fetchall()
            results = []
            for row in rows:
                try:
                    original_extracted = json.loads(row['original_extracted_data_json']) if row['original_extracted_data_json'] else {}
                except Exception:
                    original_extracted = {}
                try:
                    user_input = json.loads(row['user_input_data_json']) if row['user_input_data_json'] else {}
                except Exception:
                    user_input = {}
                try:
                    calculated = json.loads(row['calculated_financials_json']) if row['calculated_financials_json'] else {}
                except Exception:
                    calculated = {}

                results.append({
                    'id': row['id'],
                    'file_name': row['file_name'],
                    'original_file_path': row['original_file_path'],
                    'extraction_date': row['extraction_date'],
                    'raw_text_preview': row['raw_text_preview'],
                    'original_extracted_data': original_extracted,
                    'user_input_data': user_input,
                    'calculated_financials': calculated
                })
            return results
        except sqlite3.Error as e:
            logger.error(f"Error fetching all properties: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_property_details(self, property_id):
        """
        Fetches full details for a specific property by ID, including both
        original extracted data and user input data.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT original_file_path, raw_text_preview, original_extracted_data_json, user_input_data_json, calculated_financials_json FROM properties WHERE id = ?', (property_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'original_file_path': row['original_file_path'],
                    'raw_text_preview': row['raw_text_preview'],
                    'original_extracted_data': json.loads(row['original_extracted_data_json']),
                    'user_input_data': json.loads(row['user_input_data_json']), # Renamed from extracted_data
                    'calculated_financials': json.loads(row['calculated_financials_json'])
                }
            return None
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Error fetching property details for ID {property_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def delete_property(self, property_id):
        """Deletes a property from the database by its ID."""
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
            conn.commit()
            logger.info(f"Property with ID {property_id} deleted from database.")
        except sqlite3.Error as e:
            logger.error(f"Database error during deletion of property ID {property_id}: {e}", exc_info=True)
            raise # Re-raise to be caught by the caller
        finally:
            if conn:
                conn.close()

    def close(self):
        """
        This method is now mostly a placeholder as connections are closed per-operation.
        It can be kept for consistency but doesn't perform a global close anymore.
        """
        logger.info("DatabaseManager instance is being closed (individual connections are managed per operation).")

