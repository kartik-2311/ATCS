#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image Processing Module

This module handles all image processing tasks for the Animal Type Classification System,
including image capture, preprocessing, and feature extraction preparation.
"""

import os
import cv2
import numpy as np
import logging
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Class for processing animal images for classification"""
    
    def __init__(self, config=None):
        """Initialize the image processor
        
        Args:
            config (dict, optional): Configuration parameters
        """
        self.config = config or {}
        
        # Default parameters
        self.target_size = self.config.get('target_size', (640, 480))
        self.normalize = self.config.get('normalize', True)
        
        logger.info("Image processor initialized")
    
    def capture_image(self, camera_id=0):
        """Capture an image from camera
        
        Args:
            camera_id (int): Camera device ID
            
        Returns:
            numpy.ndarray: Captured image or None if failed
        """
        logger.info(f"Capturing image from camera {camera_id}")
        
        try:
            # Initialize camera
            cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                logger.error(f"Failed to open camera {camera_id}")
                return None
            
            # Capture frame
            ret, frame = cap.read()
            
            # Release camera
            cap.release()
            
            if not ret:
                logger.error("Failed to capture image")
                return None
            
            logger.info("Image captured successfully")
            return frame
            
        except Exception as e:
            logger.error(f"Error capturing image: {str(e)}")
            return None
    
    def load_image(self, image_path):
        """Load an image from file
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            numpy.ndarray: Loaded image or None if failed
        """
        logger.info(f"Loading image from {image_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Load image
            image = cv2.imread(image_path)
            
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Convert from BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            logger.info("Image loaded successfully")
            return image
            
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            return None
    
    def preprocess(self, image_input):
        """Preprocess an image for feature extraction
        
        Args:
            image_input (str or numpy.ndarray): Image path or image array
            
        Returns:
            numpy.ndarray: Preprocessed image or None if failed
        """
        logger.info("Preprocessing image")
        
        try:
            # Load image if path is provided
            if isinstance(image_input, str):
                image = self.load_image(image_input)
            else:
                image = image_input.copy()
            
            if image is None:
                return None
            
            # Resize image
            image = cv2.resize(image, self.target_size)
            
            # Apply noise reduction
            image = cv2.GaussianBlur(image, (5, 5), 0)
            
            # Enhance contrast
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            enhanced_lab = cv2.merge((cl, a, b))
            image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
            
            # Normalize if required
            if self.normalize:
                image = image.astype(np.float32) / 255.0
            
            logger.info("Image preprocessing completed")
            return image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return None
    
    def extract_animal_roi(self, image):
        """Extract region of interest containing the animal
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            numpy.ndarray: ROI containing the animal or original image if detection fails
        """
        logger.info("Extracting animal ROI")
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                logger.warning("No contours found, returning original image")
                return image
            
            # Find the largest contour (assumed to be the animal)
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Extract ROI with padding
            padding = 20
            x_start = max(0, x - padding)
            y_start = max(0, y - padding)
            x_end = min(image.shape[1], x + w + padding)
            y_end = min(image.shape[0], y + h + padding)
            
            roi = image[y_start:y_end, x_start:x_end]
            
            logger.info("Animal ROI extracted successfully")
            return roi
            
        except Exception as e:
            logger.error(f"Error extracting animal ROI: {str(e)}")
            return image
    
    def apply_perspective_correction(self, image):
        """Apply perspective correction to standardize animal orientation
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            numpy.ndarray: Perspective-corrected image
        """
        logger.info("Applying perspective correction")
        
        # This is a placeholder for more sophisticated perspective correction
        # In a real implementation, this would detect key points and correct perspective
        
        # For now, we'll just return the original image
        logger.info("Perspective correction applied (placeholder)")
        return image
    
    def save_processed_image(self, image, output_path):
        """Save processed image to file
        
        Args:
            image (numpy.ndarray): Image to save
            output_path (str): Path to save the image
            
        Returns:
            bool: Success status
        """
        logger.info(f"Saving processed image to {output_path}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Convert to uint8 if normalized
            if image.dtype == np.float32 and image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            
            # Convert from RGB to BGR for OpenCV
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Save image
            cv2.imwrite(output_path, image)
            
            logger.info("Image saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return False
    
    def get_image_metadata(self, image_path):
        """Extract metadata from image file
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Image metadata
        """
        logger.info(f"Extracting metadata from {image_path}")
        
        try:
            # Open image with PIL to extract metadata
            with Image.open(image_path) as img:
                metadata = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'filename': Path(image_path).name,
                    'filepath': image_path,
                    'filesize': os.path.getsize(image_path),
                    'timestamp': os.path.getmtime(image_path)
                }
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        metadata['exif'] = exif
            
            logger.info("Metadata extracted successfully")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {'error': str(e)}