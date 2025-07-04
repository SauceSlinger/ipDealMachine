import sqlite3
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path # Store the database file path
        # No self.conn or self.cursor here anymore
        self._create_table_if_not_exists() # Ensure table exists on init

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
        """Creates the properties table if it does not exist using a temporary connection."""
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL UNIQUE,
                    original_file_path TEXT,
                    extraction_date TEXT,
                    raw_text_preview TEXT,
                    extracted_data_json TEXT,  -- Stores all input fields as JSON
                    calculated_financials_json TEXT -- Stores all output fields as JSON
                )
            ''')
            conn.commit()
            logger.info("Database table 'properties' ensured.")
        except sqlite3.Error as e:
            logger.error(f"Error creating table: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def insert_property(self, file_name, original_file_path, raw_text_preview, extracted_data, calculated_financials):
        """
        Inserts a new property record into the database.
        A new connection is opened and closed within this method.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            extraction_date = datetime.now().isoformat()
            extracted_data_json = json.dumps(extracted_data)
            calculated_financials_json = json.dumps(calculated_financials)

            cursor.execute('''
                INSERT INTO properties (file_name, original_file_path, extraction_date, raw_text_preview, extracted_data_json, calculated_financials_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_name, original_file_path, extraction_date, raw_text_preview, extracted_data_json, calculated_financials_json))
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

    def update_property(self, property_id, file_name, original_file_path, raw_text_preview, extracted_data, calculated_financials):
        """
        Updates an existing property record in the database.
        A new connection is opened and closed within this method.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            extracted_data_json = json.dumps(extracted_data)
            calculated_financials_json = json.dumps(calculated_financials)

            cursor.execute('''
                UPDATE properties
                SET file_name = ?, original_file_path = ?, raw_text_preview = ?, extracted_data_json = ?, calculated_financials_json = ?
                WHERE id = ?
            ''', (file_name, original_file_path, raw_text_preview, extracted_data_json, calculated_financials_json, property_id))
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

    def get_property_details(self, property_id):
        """
        Fetches full details for a specific property by ID.
        A new connection is opened and closed within this method.
        """
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT original_file_path, raw_text_preview, extracted_data_json, calculated_financials_json FROM properties WHERE id = ?', (property_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'original_file_path': row['original_file_path'],
                    'raw_text_preview': row['raw_text_preview'],
                    'extracted_data': json.loads(row['extracted_data_json']),
                    'calculated_financials': json.loads(row['calculated_financials_json'])
                }
            return None
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Error fetching property details for ID {property_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def close(self):
        """
        This method is now mostly a placeholder as connections are closed per-operation.
        It can be kept for consistency but doesn't perform a global close anymore.
        """
        logger.info("DatabaseManager instance is being closed (individual connections are managed per operation).")

