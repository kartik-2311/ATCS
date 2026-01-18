#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bharat Pashudhan App (BPA) Integration Module

This module implements the integration with the Bharat Pashudhan App (BPA)
for syncing Animal Type Classification (ATC) data.
"""

import os
import json
import logging
import requests
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class BPAIntegrator:
    def sync_data(self, animal_id, scores):
        """Sync classification data with Bharat Pashudhan App (BPA). Placeholder implementation."""
        logger.info(f"Syncing data for animal_id={animal_id} with BPA (placeholder)")
        # Simulate a successful sync
        return {'success': True, 'message': 'Data synced (simulated)'}
    """Class for integrating with Bharat Pashudhan App (BPA)"""
    
    def __init__(self, config_path=None):
        """Initialize the BPA integration
        
        Args:
            config_path (str, optional): Path to configuration file
        """
        self.config_path = config_path
        self.config = {}
        self.api_base_url = ""
        self.api_key = ""
        self.user_id = ""
        self.auth_token = ""
        self.is_authenticated = False
        
        # Load configuration
        self._load_config()
        
        logger.info("BPA Integration initialized")
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_path and os.path.exists(self.config_path):
                logger.info(f"Loading BPA configuration from {self.config_path}")
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                
                # Extract configuration values
                self.api_base_url = self.config.get('api_base_url', '')
                self.api_key = self.config.get('api_key', '')
                self.user_id = self.config.get('user_id', '')
                
                # Check if auth token is stored and not expired
                auth_token = self.config.get('auth_token', '')
                token_expiry = self.config.get('token_expiry', 0)
                
                if auth_token and token_expiry > time.time():
                    self.auth_token = auth_token
                    self.is_authenticated = True
                    logger.info("Using stored authentication token")
            else:
                logger.warning("BPA configuration file not found or not specified")
                
        except Exception as e:
            logger.error(f"Error loading BPA configuration: {str(e)}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            if self.config_path:
                # Update config with current values
                self.config['api_base_url'] = self.api_base_url
                self.config['api_key'] = self.api_key
                self.config['user_id'] = self.user_id
                self.config['auth_token'] = self.auth_token
                
                # Set token expiry (24 hours from now)
                self.config['token_expiry'] = time.time() + (24 * 60 * 60)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                # Save to file
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                    
                logger.info("BPA configuration saved")
                
        except Exception as e:
            logger.error(f"Error saving BPA configuration: {str(e)}")
    
    def authenticate(self, username=None, password=None):
        """Authenticate with BPA API
        
        Args:
            username (str, optional): BPA username
            password (str, optional): BPA password
            
        Returns:
            bool: Authentication success status
        """
        logger.info("Authenticating with BPA API")
        
        try:
            # Use provided credentials or from config
            username = username or self.config.get('username', '')
            password = password or self.config.get('password', '')
            
            if not username or not password:
                logger.error("Missing authentication credentials")
                return False
            
            if not self.api_base_url:
                logger.error("API base URL not configured")
                return False
            
            # Prepare authentication request
            auth_url = f"{self.api_base_url}/auth/login"
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }
            payload = {
                'username': username,
                'password': password
            }
            
            # Send authentication request
            response = requests.post(auth_url, headers=headers, json=payload)
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                
                if 'token' in data:
                    self.auth_token = data['token']
                    self.user_id = data.get('user_id', self.user_id)
                    self.is_authenticated = True
                    
                    # Save updated configuration
                    self._save_config()
                    
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.error("Authentication response missing token")
            else:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
            
            return False
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure that we have a valid authentication token
        
        Returns:
            bool: Authentication status
        """
        if not self.is_authenticated:
            return self.authenticate()
        return True
    
    def sync_classification(self, classification_data):
        """Sync classification data with BPA
        
        Args:
            classification_data (dict): Classification data to sync
            
        Returns:
            dict: Sync result with status and message
        """
        logger.info(f"Syncing classification for animal: {classification_data.get('animal_id', 'Unknown')}")
        
        result = {
            'success': False,
            'message': "",
            'bpa_record_id': None
        }
        
        try:
            # Ensure we're authenticated
            if not self._ensure_authenticated():
                result['message'] = "Authentication failed"
                return result
            
            # Prepare API endpoint
            sync_url = f"{self.api_base_url}/atc/records"
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key,
                'Authorization': f"Bearer {self.auth_token}"
            }
            
            # Prepare payload
            payload = self._format_classification_for_bpa(classification_data)
            
            # Send sync request
            response = requests.post(sync_url, headers=headers, json=payload)
            
            # Check response
            if response.status_code in [200, 201]:
                data = response.json()
                
                result['success'] = True
                result['message'] = "Classification synced successfully"
                result['bpa_record_id'] = data.get('record_id')
                
                logger.info(f"Classification synced successfully with BPA record ID: {result['bpa_record_id']}")
            else:
                result['message'] = f"Sync failed with status code: {response.status_code}"
                logger.error(result['message'])
                logger.error(f"Response: {response.text}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error syncing classification: {str(e)}"
            logger.error(error_msg)
            result['message'] = error_msg
            return result
    
    def _format_classification_for_bpa(self, classification_data):
        """Format classification data for BPA API
        
        Args:
            classification_data (dict): Classification data
            
        Returns:
            dict: Formatted data for BPA API
        """
        # Extract relevant data
        animal_id = classification_data.get('animal_id', '')
        overall_score = classification_data.get('overall_score', 0)
        classification = classification_data.get('classification', '')
        measurements = classification_data.get('measurements', {})
        trait_scores = classification_data.get('trait_scores', {})
        
        # Format for BPA API
        formatted_data = {
            'animal_id': animal_id,
            'atc_date': classification_data.get('classification_date', datetime.now().isoformat()),
            'overall_score': overall_score,
            'classification': classification,
            'created_by': classification_data.get('created_by', self.user_id),
            'traits': []
        }
        
        # Add traits with measurements and scores
        for trait, value in measurements.items():
            trait_data = {
                'trait_name': trait,
                'measurement': value,
                'score': trait_scores.get(trait, 0)
            }
            formatted_data['traits'].append(trait_data)
        
        # Add image path if available
        if 'image_path' in classification_data and classification_data['image_path']:
            formatted_data['image_path'] = classification_data['image_path']
        
        return formatted_data
    
    def get_animal_info(self, animal_id):
        """Get animal information from BPA
        
        Args:
            animal_id (str): Animal ID
            
        Returns:
            dict: Animal information or None if not found
        """
        logger.info(f"Getting animal information from BPA for: {animal_id}")
        
        try:
            # Ensure we're authenticated
            if not self._ensure_authenticated():
                logger.error("Authentication failed")
                return None
            
            # Prepare API endpoint
            animal_url = f"{self.api_base_url}/animals/{animal_id}"
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key,
                'Authorization': f"Bearer {self.auth_token}"
            }
            
            # Send request
            response = requests.get(animal_url, headers=headers)
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Animal information retrieved successfully for: {animal_id}")
                return data
            elif response.status_code == 404:
                logger.warning(f"Animal not found in BPA: {animal_id}")
                return None
            else:
                logger.error(f"Failed to get animal information with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting animal information: {str(e)}")
            return None
    
    def get_atc_history(self, animal_id):
        """Get ATC history for an animal from BPA
        
        Args:
            animal_id (str): Animal ID
            
        Returns:
            list: ATC history records
        """
        logger.info(f"Getting ATC history from BPA for animal: {animal_id}")
        
        try:
            # Ensure we're authenticated
            if not self._ensure_authenticated():
                logger.error("Authentication failed")
                return []
            
            # Prepare API endpoint
            history_url = f"{self.api_base_url}/atc/history/{animal_id}"
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key,
                'Authorization': f"Bearer {self.auth_token}"
            }
            
            # Send request
            response = requests.get(history_url, headers=headers)
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                logger.info(f"Retrieved {len(history)} ATC history records for animal: {animal_id}")
                return history
            elif response.status_code == 404:
                logger.warning(f"No ATC history found for animal: {animal_id}")
                return []
            else:
                logger.error(f"Failed to get ATC history with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting ATC history: {str(e)}")
            return []
    
    def sync_batch(self, classifications, database):
        """Sync a batch of classifications with BPA
        
        Args:
            classifications (list): List of classification data
            database (ATCDatabase): Database instance for updating sync status
            
        Returns:
            dict: Sync statistics
        """
        logger.info(f"Syncing batch of {len(classifications)} classifications with BPA")
        
        stats = {
            'total': len(classifications),
            'success': 0,
            'failed': 0
        }
        
        for classification in classifications:
            classification_id = classification.get('id')
            animal_id = classification.get('animal_id')
            
            logger.info(f"Syncing classification {classification_id} for animal {animal_id}")
            
            # Sync with BPA
            result = self.sync_classification(classification)
            
            # Update database with sync status
            if result['success']:
                database.mark_as_synced(classification_id, "success")
                stats['success'] += 1
            else:
                database.mark_as_synced(classification_id, "failed", result['message'])
                stats['failed'] += 1
            
            # Add small delay to avoid overwhelming the API
            time.sleep(0.5)
        
        logger.info(f"Batch sync completed: {stats}")
        return stats
    
    def test_connection(self):
        """Test connection to BPA API
        
        Returns:
            bool: Connection status
        """
        logger.info("Testing connection to BPA API")
        
        try:
            # Check if API base URL is configured
            if not self.api_base_url:
                logger.error("API base URL not configured")
                return False
            
            # Prepare test endpoint
            test_url = f"{self.api_base_url}/ping"
            
            # Prepare headers
            headers = {
                'X-API-Key': self.api_key
            }
            
            # Send request
            response = requests.get(test_url, headers=headers)
            
            # Check response
            if response.status_code == 200:
                logger.info("Connection to BPA API successful")
                return True
            else:
                logger.error(f"Connection test failed with status code: {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            return False