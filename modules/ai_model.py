#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Model Module

This module implements the AI models for extracting body structure parameters
from animal images for the Animal Type Classification System.
"""

import os
import numpy as np
import tensorflow as tf
import logging
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model

logger = logging.getLogger(__name__)

class AnimalClassifier:
    """Class for AI-based animal feature extraction and classification"""
    
    def __init__(self, model_path=None):
        """Initialize the animal classifier
        
        Args:
            model_path (str, optional): Path to pre-trained model
        """
        self.model_path = model_path
        self.model = None
        self.keypoint_model = None
        self.feature_extractor = None
        
        # Initialize models
        self._initialize_models()
        
        logger.info("Animal classifier initialized")
    
    def _initialize_models(self):
        """Initialize AI models for feature extraction"""
        try:
            # Load pre-trained model if provided
            if self.model_path and os.path.exists(self.model_path):
                logger.info(f"Loading model from {self.model_path}")
                self.model = load_model(self.model_path)
            else:
                logger.info("Creating new feature extraction model")
                # Create a base feature extraction model using MobileNetV2
                base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
                x = base_model.output
                x = GlobalAveragePooling2D()(x)
                x = Dense(1024, activation='relu')(x)
                predictions = Dense(128, activation='linear')(x)  # Feature vector
                self.feature_extractor = Model(inputs=base_model.input, outputs=predictions)
                
                # Freeze base model layers
                for layer in base_model.layers:
                    layer.trainable = False
            
            # Initialize keypoint detection model
            # This would typically be a specialized model for animal body keypoints
            # For now, we'll use a placeholder
            logger.info("Initializing keypoint detection model")
            self._initialize_keypoint_model()
            
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            raise
    
    def _initialize_keypoint_model(self):
        """Initialize model for keypoint detection"""
        try:
            # In a real implementation, this would load a specialized keypoint detection model
            # For now, we'll create a simple placeholder model
            base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
            x = base_model.output
            x = GlobalAveragePooling2D()(x)
            x = Dense(512, activation='relu')(x)
            
            # Output layer for keypoints (x, y coordinates for each keypoint)
            # For cattle, we might track points like:
            # - nose, eyes, ears
            # - withers (highest point of the shoulder)
            # - back points
            # - hip bones
            # - tail
            # - legs joints
            num_keypoints = 17  # Similar to COCO human keypoints as a starting point
            keypoints = Dense(num_keypoints * 2, activation='linear')(x)  # x,y coordinates
            
            self.keypoint_model = Model(inputs=base_model.input, outputs=keypoints)
            
            # Freeze base model layers
            for layer in base_model.layers:
                layer.trainable = False
                
            logger.info("Keypoint model initialized")
            
        except Exception as e:
            logger.error(f"Error initializing keypoint model: {str(e)}")
            self.keypoint_model = None
    
    def preprocess_for_model(self, image):
        """Preprocess image for model input
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            numpy.ndarray: Preprocessed image
        """
        try:
            # Resize to model input size
            image_resized = tf.image.resize(image, (224, 224))
            
            # Normalize pixel values
            if image_resized.dtype != np.float32:
                image_resized = image_resized.astype(np.float32) / 255.0
                
            # Expand dimensions for batch
            image_batch = np.expand_dims(image_resized, axis=0)
            
            return image_batch
            
        except Exception as e:
            logger.error(f"Error preprocessing image for model: {str(e)}")
            return None
    
    def detect_keypoints(self, image):
        """Detect animal body keypoints in the image
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            dict: Detected keypoints with coordinates
        """
        logger.info("Detecting animal keypoints")
        
        try:
            if self.keypoint_model is None:
                logger.error("Keypoint model not initialized")
                return None
            
            # Preprocess image
            image_batch = self.preprocess_for_model(image)
            
            if image_batch is None:
                return None
            
            # Predict keypoints
            keypoints_flat = self.keypoint_model.predict(image_batch)[0]
            
            # Reshape to (num_keypoints, 2) for x,y coordinates
            num_keypoints = len(keypoints_flat) // 2
            keypoints = keypoints_flat.reshape(num_keypoints, 2)
            
            # Define keypoint names (these would match the training data)
            # This is a placeholder - actual keypoints would depend on the specific model
            keypoint_names = [
                'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
                'withers', 'mid_back', 'tail_base', 'tail_tip',
                'left_shoulder', 'left_elbow', 'left_knee', 'left_hoof',
                'right_shoulder', 'right_elbow', 'right_knee', 'right_hoof'
            ]
            
            # Create dictionary of keypoints
            keypoints_dict = {}
            for i, name in enumerate(keypoint_names):
                if i < len(keypoints):
                    keypoints_dict[name] = {
                        'x': float(keypoints[i, 0]),
                        'y': float(keypoints[i, 1]),
                        # In a real model, we would also have a confidence score
                        'confidence': 0.9  # Placeholder
                    }
            
            logger.info(f"Detected {len(keypoints_dict)} keypoints")
            return keypoints_dict
            
        except Exception as e:
            logger.error(f"Error detecting keypoints: {str(e)}")
            return None
    
    def extract_features(self, image):
        """Extract body structure features from the image
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            dict: Extracted features and measurements
        """
        logger.info("Extracting animal body features")
        
        try:
            # Detect keypoints
            keypoints = self.detect_keypoints(image)
            
            if keypoints is None:
                logger.error("Failed to detect keypoints")
                return None
            
            # Calculate body measurements based on keypoints
            measurements = self._calculate_measurements(keypoints, image.shape)
            
            # Combine keypoints and measurements
            features = {
                'keypoints': keypoints,
                'measurements': measurements,
                'image_shape': image.shape
            }
            
            logger.info("Feature extraction completed")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return None
    
    def _calculate_measurements(self, keypoints, image_shape):
        """Calculate body measurements from keypoints
        
        Args:
            keypoints (dict): Detected keypoints
            image_shape (tuple): Shape of the original image
            
        Returns:
            dict: Body measurements
        """
        try:
            # Extract image dimensions for scaling
            img_height, img_width = image_shape[:2]
            
            # Initialize measurements dictionary
            measurements = {}
            
            # Calculate body length (nose to tail base)
            if 'nose' in keypoints and 'tail_base' in keypoints:
                nose = keypoints['nose']
                tail_base = keypoints['tail_base']
                body_length = self._calculate_distance(nose, tail_base)
                measurements['body_length'] = body_length
            
            # Calculate height at withers
            if 'withers' in keypoints and 'left_hoof' in keypoints and 'right_hoof' in keypoints:
                withers = keypoints['withers']
                left_hoof = keypoints['left_hoof']
                right_hoof = keypoints['right_hoof']
                
                # Use the closer hoof for height calculation
                left_height = abs(withers['y'] - left_hoof['y'])
                right_height = abs(withers['y'] - right_hoof['y'])
                height_at_withers = min(left_height, right_height)
                
                measurements['height_at_withers'] = height_at_withers
            
            # Calculate chest width (between shoulders)
            if 'left_shoulder' in keypoints and 'right_shoulder' in keypoints:
                left_shoulder = keypoints['left_shoulder']
                right_shoulder = keypoints['right_shoulder']
                chest_width = self._calculate_distance(left_shoulder, right_shoulder)
                measurements['chest_width'] = chest_width
            
            # Calculate back angle
            if 'withers' in keypoints and 'mid_back' in keypoints and 'tail_base' in keypoints:
                withers = keypoints['withers']
                mid_back = keypoints['mid_back']
                tail_base = keypoints['tail_base']
                
                # Calculate angles
                back_angle = self._calculate_angle(withers, mid_back, tail_base)
                measurements['back_angle'] = back_angle
            
            # Calculate rump angle
            if 'mid_back' in keypoints and 'tail_base' in keypoints and 'tail_tip' in keypoints:
                mid_back = keypoints['mid_back']
                tail_base = keypoints['tail_base']
                tail_tip = keypoints['tail_tip']
                
                rump_angle = self._calculate_angle(mid_back, tail_base, tail_tip)
                measurements['rump_angle'] = rump_angle
            
            # Add more measurements as needed for ATC
            
            logger.info(f"Calculated {len(measurements)} body measurements")
            return measurements
            
        except Exception as e:
            logger.error(f"Error calculating measurements: {str(e)}")
            return {}
    
    def _calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points
        
        Args:
            point1 (dict): First point with x, y coordinates
            point2 (dict): Second point with x, y coordinates
            
        Returns:
            float: Distance between points
        """
        return np.sqrt((point1['x'] - point2['x'])**2 + (point1['y'] - point2['y'])**2)
    
    def _calculate_angle(self, point1, point2, point3):
        """Calculate angle between three points (in degrees)
        
        Args:
            point1 (dict): First point with x, y coordinates
            point2 (dict): Second point (vertex) with x, y coordinates
            point3 (dict): Third point with x, y coordinates
            
        Returns:
            float: Angle in degrees
        """
        # Calculate vectors
        vector1 = [point1['x'] - point2['x'], point1['y'] - point2['y']]
        vector2 = [point3['x'] - point2['x'], point3['y'] - point2['y']]
        
        # Calculate dot product
        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        
        # Calculate magnitudes
        mag1 = np.sqrt(vector1[0]**2 + vector1[1]**2)
        mag2 = np.sqrt(vector2[0]**2 + vector2[1]**2)
        
        # Calculate angle in radians and convert to degrees
        cos_angle = dot_product / (mag1 * mag2)
        # Clamp to handle floating point errors
        cos_angle = max(min(cos_angle, 1.0), -1.0)
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
    def train(self, training_data, validation_data, epochs=10, batch_size=32):
        """Train the model with new data
        
        Args:
            training_data (tuple): Training images and labels
            validation_data (tuple): Validation images and labels
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            
        Returns:
            dict: Training history
        """
        logger.info(f"Training model with {len(training_data[0])} samples")
        
        # This is a placeholder for model training
        # In a real implementation, this would train the model with the provided data
        
        logger.info("Model training completed (placeholder)")
        return {'accuracy': 0.85, 'val_accuracy': 0.82}  # Placeholder
    
    def save_model(self, save_path):
        """Save the trained model
        
        Args:
            save_path (str): Path to save the model
            
        Returns:
            bool: Success status
        """
        logger.info(f"Saving model to {save_path}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save the model
            if self.model is not None:
                self.model.save(save_path)
                logger.info("Model saved successfully")
                return True
            else:
                logger.error("No model to save")
                return False
                
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False