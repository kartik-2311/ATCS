#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Module

This module implements the database functionality for storing and retrieving
Animal Type Classification (ATC) data.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def save_record(self, record):
        """Save a classification record to the database (compatibility wrapper)."""
        return self.add_classification(record)
    """Class for managing ATC data storage and retrieval"""
    
    def __init__(self, db_path=None):
        """Initialize the database
        
        Args:
            db_path (str, optional): Path to the SQLite database file
        """
        # Set default database path if not provided
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'data', 'atc_database.db')
        
        self.db_path = db_path
        self.conn = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._initialize_db()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def _initialize_db(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            # Connect to database
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create animals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS animals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    animal_id TEXT UNIQUE,
                    tag_number TEXT,
                    breed TEXT,
                    gender TEXT,
                    birth_date TEXT,
                    owner_name TEXT,
                    owner_contact TEXT,
                    location TEXT,
                    registration_date TEXT,
                    last_updated TEXT
                )
            ''')
            
            # Create classifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    animal_id TEXT,
                    classification_date TEXT,
                    overall_score REAL,
                    classification TEXT,
                    image_path TEXT,
                    synced_to_bpa INTEGER DEFAULT 0,
                    sync_date TEXT,
                    created_by TEXT,
                    FOREIGN KEY (animal_id) REFERENCES animals (animal_id)
                )
            ''')
            
            # Create measurements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    classification_id INTEGER,
                    trait TEXT,
                    value REAL,
                    score REAL,
                    FOREIGN KEY (classification_id) REFERENCES classifications (id)
                )
            ''')
            
            # Create sync_log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    animal_id TEXT,
                    classification_id INTEGER,
                    sync_date TEXT,
                    sync_status TEXT,
                    error_message TEXT,
                    FOREIGN KEY (animal_id) REFERENCES animals (animal_id),
                    FOREIGN KEY (classification_id) REFERENCES classifications (id)
                )
            ''')
            
            # Commit changes
            self.conn.commit()
            logger.info("Database tables created successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            if self.conn:
                self.conn.rollback()
            raise
    
    def _get_connection(self):
        """Get a database connection
        
        Returns:
            sqlite3.Connection: Database connection
        """
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return self.conn
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    def add_animal(self, animal_data):
        """Add a new animal to the database
        
        Args:
            animal_data (dict): Animal information
            
        Returns:
            str: Animal ID if successful, None otherwise
        """
        logger.info(f"Adding new animal: {animal_data.get('tag_number', 'Unknown')}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Generate animal_id if not provided
            if 'animal_id' not in animal_data or not animal_data['animal_id']:
                animal_data['animal_id'] = f"ATC-{datetime.now().strftime('%Y%m%d%H%M%S')}" 
            
            # Set registration and update dates
            current_time = datetime.now().isoformat()
            if 'registration_date' not in animal_data or not animal_data['registration_date']:
                animal_data['registration_date'] = current_time
            animal_data['last_updated'] = current_time
            
            # Insert animal data
            cursor.execute('''
                INSERT INTO animals (
                    animal_id, tag_number, breed, gender, birth_date,
                    owner_name, owner_contact, location, registration_date, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                animal_data.get('animal_id'),
                animal_data.get('tag_number'),
                animal_data.get('breed'),
                animal_data.get('gender'),
                animal_data.get('birth_date'),
                animal_data.get('owner_name'),
                animal_data.get('owner_contact'),
                animal_data.get('location'),
                animal_data.get('registration_date'),
                animal_data.get('last_updated')
            ))
            
            # Commit changes
            conn.commit()
            logger.info(f"Animal added successfully with ID: {animal_data['animal_id']}")
            
            return animal_data['animal_id']
            
        except sqlite3.Error as e:
            logger.error(f"Error adding animal: {str(e)}")
            if conn:
                conn.rollback()
            return None
    
    def update_animal(self, animal_id, animal_data):
        """Update an existing animal in the database
        
        Args:
            animal_id (str): Animal ID to update
            animal_data (dict): Updated animal information
            
        Returns:
            bool: Success status
        """
        logger.info(f"Updating animal: {animal_id}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Set update date
            animal_data['last_updated'] = datetime.now().isoformat()
            
            # Build update query dynamically based on provided fields
            fields = []
            values = []
            
            for key, value in animal_data.items():
                if key != 'animal_id':  # Skip animal_id as it's the identifier
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            # Add animal_id as the last parameter
            values.append(animal_id)
            
            # Execute update query
            cursor.execute(f'''
                UPDATE animals SET {', '.join(fields)} WHERE animal_id = ?
            ''', values)
            
            # Commit changes
            conn.commit()
            
            # Check if animal was updated
            if cursor.rowcount > 0:
                logger.info(f"Animal {animal_id} updated successfully")
                return True
            else:
                logger.warning(f"Animal {animal_id} not found")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Error updating animal: {str(e)}")
            if conn:
                conn.rollback()
            return False
    
    def get_animal(self, animal_id):
        """Get animal information by ID
        
        Args:
            animal_id (str): Animal ID to retrieve
            
        Returns:
            dict: Animal information
        """
        logger.info(f"Retrieving animal: {animal_id}")
        
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query animal data
            cursor.execute('''
                SELECT * FROM animals WHERE animal_id = ?
            ''', (animal_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Convert row to dictionary
                animal = dict(row)
                logger.info(f"Animal {animal_id} retrieved successfully")
                return animal
            else:
                logger.warning(f"Animal {animal_id} not found")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving animal: {str(e)}")
            return None
    
    def search_animals(self, search_criteria):
        """Search for animals based on criteria
        
        Args:
            search_criteria (dict): Search criteria
            
        Returns:
            list: Matching animals
        """
        logger.info(f"Searching animals with criteria: {search_criteria}")
        
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query based on search criteria
            query = "SELECT * FROM animals WHERE 1=1"
            params = []
            
            for key, value in search_criteria.items():
                if value:
                    query += f" AND {key} LIKE ?"
                    params.append(f"%{value}%")
            
            # Execute query
            cursor.execute(query, params)
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            animals = [dict(row) for row in rows]
            
            logger.info(f"Found {len(animals)} animals matching criteria")
            return animals
            
        except sqlite3.Error as e:
            logger.error(f"Error searching animals: {str(e)}")
            return []
    
    def add_classification(self, classification_data):
        """Add a new classification to the database
        
        Args:
            classification_data (dict): Classification information including measurements
            
        Returns:
            int: Classification ID if successful, None otherwise
        """
        logger.info(f"Adding classification for animal: {classification_data.get('animal_id', 'Unknown')}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Set classification date if not provided
            if 'classification_date' not in classification_data or not classification_data['classification_date']:
                classification_data['classification_date'] = datetime.now().isoformat()
            
            # Insert classification data
            cursor.execute('''
                INSERT INTO classifications (
                    animal_id, classification_date, overall_score, classification,
                    image_path, synced_to_bpa, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                classification_data.get('animal_id'),
                classification_data.get('classification_date'),
                classification_data.get('overall_score'),
                classification_data.get('classification'),
                classification_data.get('image_path'),
                0,  # Not synced to BPA initially
                classification_data.get('created_by')
            ))
            
            # Get the ID of the inserted classification
            classification_id = cursor.lastrowid
            
            # Insert measurements if provided
            if 'measurements' in classification_data and 'trait_scores' in classification_data:
                measurements = classification_data['measurements']
                trait_scores = classification_data['trait_scores']
                
                for trait, value in measurements.items():
                    score = trait_scores.get(trait, 0)
                    
                    cursor.execute('''
                        INSERT INTO measurements (
                            classification_id, trait, value, score
                        ) VALUES (?, ?, ?, ?)
                    ''', (classification_id, trait, value, score))
            
            # Commit changes
            conn.commit()
            logger.info(f"Classification added successfully with ID: {classification_id}")
            
            return classification_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding classification: {str(e)}")
            if conn:
                conn.rollback()
            return None
    
    def get_classification(self, classification_id):
        """Get classification information by ID
        
        Args:
            classification_id (int): Classification ID to retrieve
            
        Returns:
            dict: Classification information with measurements
        """
        logger.info(f"Retrieving classification: {classification_id}")
        
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query classification data
            cursor.execute('''
                SELECT * FROM classifications WHERE id = ?
            ''', (classification_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Convert row to dictionary
                classification = dict(row)
                
                # Query measurements for this classification
                cursor.execute('''
                    SELECT trait, value, score FROM measurements WHERE classification_id = ?
                ''', (classification_id,))
                
                measurement_rows = cursor.fetchall()
                
                # Add measurements to classification
                measurements = {}
                trait_scores = {}
                
                for m_row in measurement_rows:
                    measurements[m_row['trait']] = m_row['value']
                    trait_scores[m_row['trait']] = m_row['score']
                
                classification['measurements'] = measurements
                classification['trait_scores'] = trait_scores
                
                logger.info(f"Classification {classification_id} retrieved successfully")
                return classification
            else:
                logger.warning(f"Classification {classification_id} not found")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving classification: {str(e)}")
            return None
    
    def get_animal_classifications(self, animal_id):
        """Get all classifications for an animal
        
        Args:
            animal_id (str): Animal ID
            
        Returns:
            list: Classification records
        """
        logger.info(f"Retrieving classifications for animal: {animal_id}")
        
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query classifications
            cursor.execute('''
                SELECT * FROM classifications WHERE animal_id = ? ORDER BY classification_date DESC
            ''', (animal_id,))
            
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            classifications = []
            
            for row in rows:
                classification = dict(row)
                
                # Query measurements for this classification
                cursor.execute('''
                    SELECT trait, value, score FROM measurements WHERE classification_id = ?
                ''', (classification['id'],))
                
                measurement_rows = cursor.fetchall()
                
                # Add measurements to classification
                measurements = {}
                trait_scores = {}
                
                for m_row in measurement_rows:
                    measurements[m_row['trait']] = m_row['value']
                    trait_scores[m_row['trait']] = m_row['score']
                
                classification['measurements'] = measurements
                classification['trait_scores'] = trait_scores
                
                classifications.append(classification)
            
            logger.info(f"Retrieved {len(classifications)} classifications for animal {animal_id}")
            return classifications
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving animal classifications: {str(e)}")
            return []
    
    def mark_as_synced(self, classification_id, sync_status="success", error_message=None):
        """Mark a classification as synced to BPA
        
        Args:
            classification_id (int): Classification ID
            sync_status (str): Sync status (success/failed)
            error_message (str, optional): Error message if sync failed
            
        Returns:
            bool: Success status
        """
        logger.info(f"Marking classification {classification_id} as synced with status: {sync_status}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get animal_id for the classification
            cursor.execute('''
                SELECT animal_id FROM classifications WHERE id = ?
            ''', (classification_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Classification {classification_id} not found")
                return False
            
            animal_id = row['animal_id']
            sync_date = datetime.now().isoformat()
            
            # Update classification sync status
            if sync_status == "success":
                cursor.execute('''
                    UPDATE classifications SET synced_to_bpa = 1, sync_date = ? WHERE id = ?
                ''', (sync_date, classification_id))
            
            # Add entry to sync log
            cursor.execute('''
                INSERT INTO sync_log (
                    animal_id, classification_id, sync_date, sync_status, error_message
                ) VALUES (?, ?, ?, ?, ?)
            ''', (animal_id, classification_id, sync_date, sync_status, error_message))
            
            # Commit changes
            conn.commit()
            logger.info(f"Classification {classification_id} marked as synced")
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error marking classification as synced: {str(e)}")
            if conn:
                conn.rollback()
            return False
    
    def get_unsynced_classifications(self, limit=10):
        """Get classifications not yet synced to BPA
        
        Args:
            limit (int): Maximum number of records to return
            
        Returns:
            list: Unsynced classification records
        """
        logger.info(f"Retrieving up to {limit} unsynced classifications")
        
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query unsynced classifications
            cursor.execute('''
                SELECT * FROM classifications WHERE synced_to_bpa = 0 ORDER BY classification_date ASC LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries and add measurements
            classifications = []
            
            for row in rows:
                classification = dict(row)
                
                # Query measurements for this classification
                cursor.execute('''
                    SELECT trait, value, score FROM measurements WHERE classification_id = ?
                ''', (classification['id'],))
                
                measurement_rows = cursor.fetchall()
                
                # Add measurements to classification
                measurements = {}
                trait_scores = {}
                
                for m_row in measurement_rows:
                    measurements[m_row['trait']] = m_row['value']
                    trait_scores[m_row['trait']] = m_row['score']
                
                classification['measurements'] = measurements
                classification['trait_scores'] = trait_scores
                
                classifications.append(classification)
            
            logger.info(f"Retrieved {len(classifications)} unsynced classifications")
            return classifications
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving unsynced classifications: {str(e)}")
            return []
    
    def export_data(self, export_path, start_date=None, end_date=None):
        """Export database data to JSON file
        
        Args:
            export_path (str): Path to export file
            start_date (str, optional): Start date for filtering (ISO format)
            end_date (str, optional): End date for filtering (ISO format)
            
        Returns:
            bool: Success status
        """
        logger.info(f"Exporting database data to {export_path}")
        
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query with date filters if provided
            query = "SELECT * FROM animals"
            params = []
            
            if start_date or end_date:
                query += " WHERE 1=1"
                
                if start_date:
                    query += " AND registration_date >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND registration_date <= ?"
                    params.append(end_date)
            
            # Query animals
            cursor.execute(query, params)
            animal_rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            animals = []
            
            for animal_row in animal_rows:
                animal = dict(animal_row)
                animal_id = animal['animal_id']
                
                # Get classifications for this animal
                cursor.execute('''
                    SELECT * FROM classifications WHERE animal_id = ?
                ''', (animal_id,))
                
                classification_rows = cursor.fetchall()
                classifications = []
                
                for class_row in classification_rows:
                    classification = dict(class_row)
                    classification_id = classification['id']
                    
                    # Get measurements for this classification
                    cursor.execute('''
                        SELECT trait, value, score FROM measurements WHERE classification_id = ?
                    ''', (classification_id,))
                    
                    measurement_rows = cursor.fetchall()
                    
                    # Add measurements to classification
                    measurements = {}
                    trait_scores = {}
                    
                    for m_row in measurement_rows:
                        measurements[m_row['trait']] = m_row['value']
                        trait_scores[m_row['trait']] = m_row['score']
                    
                    classification['measurements'] = measurements
                    classification['trait_scores'] = trait_scores
                    
                    classifications.append(classification)
                
                animal['classifications'] = classifications
                animals.append(animal)
            
            # Create export data structure
            export_data = {
                'export_date': datetime.now().isoformat(),
                'start_date': start_date,
                'end_date': end_date,
                'animals': animals
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Write to file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(animals)} animals with their classifications")
            return True
            
        except (sqlite3.Error, IOError) as e:
            logger.error(f"Error exporting database data: {str(e)}")
            return False
    
    def import_data(self, import_path, overwrite=False):
        """Import data from JSON file
        
        Args:
            import_path (str): Path to import file
            overwrite (bool): Whether to overwrite existing records
            
        Returns:
            dict: Import statistics
        """
        logger.info(f"Importing data from {import_path}")
        
        stats = {
            'animals_added': 0,
            'animals_updated': 0,
            'classifications_added': 0,
            'errors': 0
        }
        
        try:
            # Check if file exists
            if not os.path.exists(import_path):
                logger.error(f"Import file not found: {import_path}")
                return stats
            
            # Load data from file
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            conn = self._get_connection()
            
            # Process animals
            for animal in import_data.get('animals', []):
                animal_id = animal.get('animal_id')
                
                if not animal_id:
                    logger.warning("Skipping animal with no ID")
                    stats['errors'] += 1
                    continue
                
                # Check if animal exists
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM animals WHERE animal_id = ?", (animal_id,))
                exists = cursor.fetchone() is not None
                
                try:
                    if exists:
                        if overwrite:
                            # Update existing animal
                            self.update_animal(animal_id, animal)
                            stats['animals_updated'] += 1
                    else:
                        # Add new animal
                        self.add_animal(animal)
                        stats['animals_added'] += 1
                    
                    # Process classifications
                    classifications = animal.pop('classifications', [])
                    
                    for classification in classifications:
                        classification['animal_id'] = animal_id
                        
                        # Add classification
                        classification_id = self.add_classification(classification)
                        
                        if classification_id:
                            stats['classifications_added'] += 1
                        else:
                            stats['errors'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing animal {animal_id}: {str(e)}")
                    stats['errors'] += 1
            
            logger.info(f"Import completed: {stats}")
            return stats
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error importing data: {str(e)}")
            stats['errors'] += 1
            return stats