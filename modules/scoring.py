#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scoring Module

This module implements the scoring algorithms for Animal Type Classification (ATC)
based on extracted body structure parameters.
"""

import logging
import numpy as np
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ScoringSystem:
    def generate_scores(self, features, breed=None, animal_id=None):
        """Generate classification scores for an animal (compatibility wrapper)."""
        # If breed is not provided, try to get from features
        if breed is None:
            breed = features.get('breed', 'unknown')
        measurements = features.get('measurements', features)
        return self.score_animal(measurements, breed, animal_id)
    """Class for scoring animal traits according to ATC guidelines"""
    
    def __init__(self, config_path=None):
        """Initialize the ATC scorer
        
        Args:
            config_path (str, optional): Path to scoring configuration file
        """
        self.config_path = config_path
        self.scoring_config = {}
        self.trait_weights = {}
        self.breed_standards = {}
        
        # Load configuration
        self._load_config()
        
        logger.info("ATC Scorer initialized")
    
    def _load_config(self):
        """Load scoring configuration from file"""
        try:
            if self.config_path and os.path.exists(self.config_path):
                logger.info(f"Loading scoring configuration from {self.config_path}")
                with open(self.config_path, 'r') as f:
                    self.scoring_config = json.load(f)
                
                # Extract trait weights and breed standards
                self.trait_weights = self.scoring_config.get('trait_weights', {})
                self.breed_standards = self.scoring_config.get('breed_standards', {})
            else:
                logger.info("Using default scoring configuration")
                self._set_default_config()
                
        except Exception as e:
            logger.error(f"Error loading scoring configuration: {str(e)}")
            logger.info("Falling back to default configuration")
            self._set_default_config()
    
    def _set_default_config(self):
        """Set default scoring configuration"""
        # Default trait weights for ATC
        self.trait_weights = {
            'body_length': 0.15,
            'height_at_withers': 0.15,
            'chest_width': 0.10,
            'back_angle': 0.15,
            'rump_angle': 0.15,
            'leg_structure': 0.15,
            'overall_proportion': 0.15
        }
        
        # Default breed standards (simplified example)
        # In a real system, this would be much more comprehensive
        self.breed_standards = {
            'gir': {
                'body_length': {'ideal': 160, 'range': 20},
                'height_at_withers': {'ideal': 140, 'range': 15},
                'chest_width': {'ideal': 50, 'range': 10},
                'back_angle': {'ideal': 175, 'range': 10},
                'rump_angle': {'ideal': 160, 'range': 15}
            },
            'sahiwal': {
                'body_length': {'ideal': 155, 'range': 20},
                'height_at_withers': {'ideal': 135, 'range': 15},
                'chest_width': {'ideal': 48, 'range': 10},
                'back_angle': {'ideal': 170, 'range': 10},
                'rump_angle': {'ideal': 155, 'range': 15}
            },
            'murrah': {  # Buffalo breed
                'body_length': {'ideal': 165, 'range': 25},
                'height_at_withers': {'ideal': 145, 'range': 20},
                'chest_width': {'ideal': 55, 'range': 12},
                'back_angle': {'ideal': 172, 'range': 12},
                'rump_angle': {'ideal': 158, 'range': 15}
            },
            # Add more breeds as needed
        }
        
        # Combine into scoring config
        self.scoring_config = {
            'trait_weights': self.trait_weights,
            'breed_standards': self.breed_standards,
            'scoring_scale': {
                'excellent': {'min': 90, 'max': 100},
                'very_good': {'min': 80, 'max': 89},
                'good': {'min': 70, 'max': 79},
                'fair': {'min': 60, 'max': 69},
                'poor': {'min': 0, 'max': 59}
            }
        }
        
        logger.info("Default scoring configuration set")
    
    def score_animal(self, measurements, breed, animal_id=None):
        """Score animal traits based on measurements
        
        Args:
            measurements (dict): Body measurements extracted from image
            breed (str): Animal breed for standard comparison
            animal_id (str, optional): Unique identifier for the animal
            
        Returns:
            dict: Trait scores and overall classification
        """
        logger.info(f"Scoring animal traits for breed: {breed}")
        
        try:
            # Normalize breed name
            breed = breed.lower()
            
            # Check if breed standards exist
            if breed not in self.breed_standards:
                logger.warning(f"No standards found for breed: {breed}. Using generic standards.")
                breed = next(iter(self.breed_standards))  # Use first available breed as fallback
            
            # Get breed standards
            standards = self.breed_standards[breed]
            
            # Initialize scores dictionary
            trait_scores = {}
            
            # Score each trait
            for trait, weight in self.trait_weights.items():
                if trait in measurements and trait in standards:
                    # Get measurement and standard
                    measurement = measurements[trait]
                    standard = standards[trait]
                    
                    # Calculate score based on proximity to ideal value
                    score = self._calculate_trait_score(measurement, standard)
                    trait_scores[trait] = score
                else:
                    # If trait is missing, assign a default score
                    logger.warning(f"Missing measurement or standard for trait: {trait}")
                    trait_scores[trait] = 60  # Default 'fair' score
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(trait_scores)
            
            # Determine classification
            classification = self._classify_score(overall_score)
            
            # Create result dictionary
            result = {
                'animal_id': animal_id,
                'breed': breed,
                'timestamp': datetime.now().isoformat(),
                'trait_scores': trait_scores,
                'overall_score': overall_score,
                'classification': classification,
                'measurements': measurements
            }
            
            logger.info(f"Animal scored with overall score: {overall_score}, classification: {classification}")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring animal: {str(e)}")
            return None
    
    def _calculate_trait_score(self, measurement, standard):
        """Calculate score for a single trait
        
        Args:
            measurement (float): Measured value
            standard (dict): Standard with ideal value and acceptable range
            
        Returns:
            float: Score between 0 and 100
        """
        try:
            ideal = standard['ideal']
            range_val = standard['range']
            
            # Calculate deviation from ideal (as percentage of range)
            deviation = abs(measurement - ideal) / range_val
            
            # Convert to score (100 = perfect match, decreasing as deviation increases)
            # Using a sigmoid-like function to score traits
            if deviation <= 0.5:  # Within half of acceptable range
                score = 100 - (deviation * 40)  # 100 to 80
            elif deviation <= 1.0:  # Within full acceptable range
                score = 80 - ((deviation - 0.5) * 40)  # 80 to 60
            elif deviation <= 1.5:  # Within 1.5x of acceptable range
                score = 60 - ((deviation - 1.0) * 40)  # 60 to 40
            else:  # Beyond 1.5x of acceptable range
                score = max(40 - ((deviation - 1.5) * 20), 0)  # 40 to 0
            
            return round(score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating trait score: {str(e)}")
            return 50  # Default middle score
    
    def _calculate_overall_score(self, trait_scores):
        """Calculate overall score based on weighted trait scores
        
        Args:
            trait_scores (dict): Individual trait scores
            
        Returns:
            float: Overall score between 0 and 100
        """
        try:
            weighted_sum = 0
            weight_sum = 0
            
            for trait, score in trait_scores.items():
                if trait in self.trait_weights:
                    weight = self.trait_weights[trait]
                    weighted_sum += score * weight
                    weight_sum += weight
            
            # Normalize by total weight
            if weight_sum > 0:
                overall_score = weighted_sum / weight_sum
            else:
                overall_score = 0
                
            return round(overall_score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {str(e)}")
            return 0
    
    def _classify_score(self, score):
        """Classify score according to ATC standards
        
        Args:
            score (float): Overall score
            
        Returns:
            str: Classification (excellent, very_good, good, fair, poor)
        """
        try:
            scale = self.scoring_config.get('scoring_scale', {})
            
            for classification, range_vals in scale.items():
                if range_vals['min'] <= score <= range_vals['max']:
                    return classification
            
            return 'unclassified'
            
        except Exception as e:
            logger.error(f"Error classifying score: {str(e)}")
            return 'error'
    
    def get_improvement_suggestions(self, scores, breed):
        """Generate improvement suggestions based on scores
        
        Args:
            scores (dict): Trait scores
            breed (str): Animal breed
            
        Returns:
            dict: Suggestions for improvement
        """
        logger.info("Generating improvement suggestions")
        
        try:
            # Normalize breed name
            breed = breed.lower()
            
            # Check if breed standards exist
            if breed not in self.breed_standards:
                logger.warning(f"No standards found for breed: {breed}. Using generic standards.")
                breed = next(iter(self.breed_standards))  # Use first available breed as fallback
            
            # Get breed standards
            standards = self.breed_standards[breed]
            
            # Find lowest scoring traits
            trait_scores = scores.get('trait_scores', {})
            sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1])
            
            # Generate suggestions for the lowest scoring traits
            suggestions = {}
            for trait, score in sorted_traits[:3]:  # Focus on top 3 issues
                if score < 70 and trait in standards:  # Only suggest improvements for traits below 'good'
                    suggestions[trait] = self._generate_trait_suggestion(trait, score, standards[trait])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            return {}
    
    def _generate_trait_suggestion(self, trait, score, standard):
        """Generate suggestion for improving a specific trait
        
        Args:
            trait (str): Trait name
            score (float): Current score
            standard (dict): Breed standard for the trait
            
        Returns:
            str: Improvement suggestion
        """
        # This is a simplified example - in a real system, these would be more detailed
        # and specific to the trait and breed
        
        trait_suggestions = {
            'body_length': "Consider selecting animals with improved body length for breeding.",
            'height_at_withers': "Focus on height at withers in your breeding program.",
            'chest_width': "Improve chest width through selective breeding.",
            'back_angle': "Select for animals with better back conformation.",
            'rump_angle': "Improve rump angle through targeted breeding.",
            'leg_structure': "Focus on leg structure in your selection criteria.",
            'overall_proportion': "Select for animals with better overall body proportions."
        }
        
        # Get generic suggestion for the trait
        suggestion = trait_suggestions.get(trait, f"Improve {trait} through selective breeding.")
        
        # Add score context
        if score < 50:
            severity = "significant improvement needed"
        elif score < 60:
            severity = "moderate improvement needed"
        else:
            severity = "minor improvement needed"
        
        return f"{suggestion} ({severity})"
    
    def save_scoring_data(self, scores, file_path):
        """Save scoring data to file
        
        Args:
            scores (dict): Scoring results
            file_path (str): Path to save the data
            
        Returns:
            bool: Success status
        """
        logger.info(f"Saving scoring data to {file_path}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save data as JSON
            with open(file_path, 'w') as f:
                json.dump(scores, f, indent=2)
                
            logger.info("Scoring data saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scoring data: {str(e)}")
            return False
    
    def load_scoring_data(self, file_path):
        """Load scoring data from file
        
        Args:
            file_path (str): Path to the data file
            
        Returns:
            dict: Scoring data
        """
        logger.info(f"Loading scoring data from {file_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            # Load data from JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            logger.info("Scoring data loaded successfully")
            return data
            
        except Exception as e:
            logger.error(f"Error loading scoring data: {str(e)}")
            return None