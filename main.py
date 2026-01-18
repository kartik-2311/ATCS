#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Animal Type Classification System

This is the main application file for the AI-based Auto Recording of Animal Type Classification System.
It integrates all components of the system including image processing, AI model, database, and UI.

Developed for the Rashtriya Gokul Mission (RGM) under the Government of India.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Import custom modules
from modules.image_processor import ImageProcessor
from modules.ai_model import AnimalClassifier
from modules.database import DatabaseManager
from modules.scoring import ScoringSystem
from modules.ui import UserInterface
from modules.bpa_integration import BPAIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("atc_system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ATCSystem:
    def get_animal_info(self, animal_id):
        """Retrieve animal information by ID"""
        return self.db_manager.get_animal(animal_id)
    """Main class for the Animal Type Classification System"""
    
    def __init__(self, config_path=None):
        """Initialize the ATC System components
        Args:
            config_path (str, optional): Path to configuration file
        """
        logger.info("Initializing Animal Type Classification System")
        self.config_path = config_path
        # Initialize components
        self.image_processor = ImageProcessor()
        self.ai_model = AnimalClassifier()
        self.db_manager = DatabaseManager()
        self.scoring_system = ScoringSystem()
        self.ui = UserInterface(self)
        self.bpa_integrator = BPAIntegrator()
        logger.info("System initialization complete")
    
    def process_image(self, image_path):
        """Process an animal image and extract features
        
        Args:
            image_path (str): Path to the animal image file
            
        Returns:
            dict: Extracted features and measurements
        """
        logger.info(f"Processing image: {image_path}")
        
        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Process the image
        processed_image = self.image_processor.preprocess(image_path)
        
        # Extract features using AI model
        features = self.ai_model.extract_features(processed_image)
        
        return features
    
    def classify_animal(self, features):
        """Generate classification scores based on extracted features
        
        Args:
            features (dict): Extracted features and measurements
            
        Returns:
            dict: Classification scores for different body parameters
        """
        logger.info("Generating classification scores")
        
        # Generate scores
        scores = self.scoring_system.generate_scores(features)
        
        return scores
    
    def save_classification(self, animal_id, features, scores):
        """Save classification data to database
        
        Args:
            animal_id (str): Unique identifier for the animal
            features (dict): Extracted features and measurements
            scores (dict): Classification scores
            
        Returns:
            bool: Success status
        """
        logger.info(f"Saving classification data for animal ID: {animal_id}")
        
        # Create record
        record = {
            'animal_id': animal_id,
            'features': features,
            'scores': scores,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to database
        success = self.db_manager.save_record(record)
        
        if success:
            logger.info("Classification data saved successfully")
        else:
            logger.error("Failed to save classification data")
        
        return success
    
    def sync_with_bpa(self, animal_id, scores):
        """Sync classification data with Bharat Pashudhan App
        
        Args:
            animal_id (str): Unique identifier for the animal
            scores (dict): Classification scores
            
        Returns:
            bool: Success status
        """
        logger.info(f"Syncing data with BPA for animal ID: {animal_id}")
        
        # Attempt to sync with BPA
        success = self.bpa_integrator.sync_data(animal_id, scores)
        
        if success:
            logger.info("Data synced with BPA successfully")
        else:
            logger.warning("Failed to sync data with BPA")
        
        return success
    
    def run(self):
        """Run the main application"""
        logger.info("Starting Animal Type Classification System")
        
        # Start the UI
        self.ui.start()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Animal Type Classification System')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    
    return parser.parse_args()


if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    # Set debug level if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Create and run the system
    system = ATCSystem(config_path=args.config)
    system.run()