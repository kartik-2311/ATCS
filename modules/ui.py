#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User Interface Module

This module implements the user interface for the Animal Type Classification System,
designed to be user-friendly for field personnel with minimal technical skills.
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from datetime import datetime
import threading
import queue
import json

logger = logging.getLogger(__name__)

class UserInterface:
    """Main user interface class for Animal Type Classification"""
    
    def __init__(self, system):
        """Initialize the user interface
        
        Args:
            system: ATCSystem instance
        """
        self.system = system
        self.root = None
        self.camera_source = 0  # Default camera
        self.camera_active = False
        self.camera_thread = None
        self.frame_queue = queue.Queue(maxsize=10)
        self.current_image = None
        self.current_image_path = None
        self.current_animal_id = None
        self.current_breed = None
        self.current_classification = None
        
        # UI components
        self.image_panel = None
        self.status_label = None
        self.breed_var = None
        self.animal_id_var = None
        self.score_labels = {}
        self.measurement_labels = {}
        
        logger.info("User interface initialized")
    
    def start(self):
        """Start the user interface"""
        logger.info("Starting user interface")
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Animal Type Classification System")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set up the UI layout
        self._setup_ui()
        
        # Start the main loop
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _setup_ui(self):
        """Set up the user interface layout"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create top frame for controls
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        # Create animal info frame
        info_frame = ttk.LabelFrame(top_frame, text="Animal Information")
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Animal ID
        ttk.Label(info_frame, text="Animal ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.animal_id_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.animal_id_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Button(info_frame, text="Search", command=self._search_animal).grid(row=0, column=2, padx=5, pady=2)
        
        # Breed selection
        ttk.Label(info_frame, text="Breed:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.breed_var = tk.StringVar()
        breeds = ["Gir", "Sahiwal", "Murrah", "Other"]  # Example breeds
        breed_combo = ttk.Combobox(info_frame, textvariable=self.breed_var, values=breeds, width=18)
        breed_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        breed_combo.current(0)  # Set default selection
        
        # Camera controls frame
        camera_frame = ttk.LabelFrame(top_frame, text="Camera Controls")
        camera_frame.pack(side=tk.RIGHT, fill=tk.X, padx=5)
        
        # Camera buttons
        ttk.Button(camera_frame, text="Start Camera", command=self._start_camera).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(camera_frame, text="Capture", command=self._capture_image).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(camera_frame, text="Load Image", command=self._load_image).grid(row=0, column=2, padx=5, pady=5)
        
        # Create middle frame with image and results
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Image panel on the left
        image_frame = ttk.LabelFrame(middle_frame, text="Animal Image")
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create a canvas for the image with scrollbars
        image_canvas = tk.Canvas(image_frame, bg="black")
        image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder for image panel
        self.image_panel = ttk.Label(image_canvas)
        image_canvas.create_window(0, 0, anchor=tk.NW, window=self.image_panel)
        
        # Results panel on the right
        results_frame = ttk.LabelFrame(middle_frame, text="Classification Results")
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create a canvas with scrollbar for results
        results_canvas = tk.Canvas(results_frame)
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_canvas.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_canvas.configure(yscrollcommand=results_scrollbar.set)
        
        # Frame inside canvas for results content
        results_content = ttk.Frame(results_canvas)
        results_canvas.create_window((0, 0), window=results_content, anchor=tk.NW)
        
        # Overall score and classification
        ttk.Label(results_content, text="Overall Score:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.overall_score_label = ttk.Label(results_content, text="-", font=("Arial", 12))
        self.overall_score_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(results_content, text="Classification:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.classification_label = ttk.Label(results_content, text="-", font=("Arial", 12))
        self.classification_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Separator
        ttk.Separator(results_content, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Trait scores section
        ttk.Label(results_content, text="Trait Scores", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Initialize score labels for traits
        traits = ["Body Length", "Height at Withers", "Chest Width", "Back Angle", "Rump Angle", "Leg Structure", "Overall Proportion"]
        for i, trait in enumerate(traits):
            ttk.Label(results_content, text=f"{trait}:", font=("Arial", 10)).grid(row=i+4, column=0, sticky=tk.W, padx=5, pady=2)
            self.score_labels[trait.lower().replace(" ", "_")] = ttk.Label(results_content, text="-")
            self.score_labels[trait.lower().replace(" ", "_")].grid(row=i+4, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Separator
        ttk.Separator(results_content, orient=tk.HORIZONTAL).grid(row=len(traits)+4, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Measurements section
        ttk.Label(results_content, text="Measurements", font=("Arial", 12, "bold")).grid(row=len(traits)+5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Initialize measurement labels
        for i, trait in enumerate(traits):
            ttk.Label(results_content, text=f"{trait}:", font=("Arial", 10)).grid(row=i+len(traits)+6, column=0, sticky=tk.W, padx=5, pady=2)
            self.measurement_labels[trait.lower().replace(" ", "_")] = ttk.Label(results_content, text="-")
            self.measurement_labels[trait.lower().replace(" ", "_")].grid(row=i+len(traits)+6, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Update scrollregion when the results content changes size
        results_content.bind("<Configure>", lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all")))
        
        # Create bottom frame for action buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        # Action buttons
        ttk.Button(bottom_frame, text="Classify", command=self._classify_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Save Results", command=self._save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Sync with BPA", command=self._sync_with_bpa).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Clear", command=self._clear_all).pack(side=tk.LEFT, padx=5)
        
        # Status bar at the bottom
        self.status_label = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _start_camera(self):
        """Start the camera feed"""
        if self.camera_active:
            self._set_status("Camera already active")
            return
        
        try:
            # Start camera in a separate thread
            self.camera_active = True
            self.camera_thread = threading.Thread(target=self._camera_thread_func)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            
            # Start updating the UI with camera frames
            self._update_camera_feed()
            
            self._set_status("Camera started")
            
        except Exception as e:
            self.camera_active = False
            error_msg = f"Error starting camera: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Camera Error", error_msg)
    
    def _camera_thread_func(self):
        """Camera thread function to capture frames"""
        try:
            # Open camera
            cap = cv2.VideoCapture(self.camera_source)
            
            if not cap.isOpened():
                raise Exception("Could not open camera")
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            while self.camera_active:
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning("Failed to capture frame")
                    continue
                
                # Convert to RGB for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Put frame in queue for UI thread
                if not self.frame_queue.full():
                    self.frame_queue.put(frame_rgb)
            
            # Release camera when done
            cap.release()
            
        except Exception as e:
            logger.error(f"Camera thread error: {str(e)}")
            self.camera_active = False
    
    def _update_camera_feed(self):
        """Update the UI with camera frames"""
        if not self.camera_active:
            return
        
        try:
            # Get frame from queue if available
            if not self.frame_queue.empty():
                frame = self.frame_queue.get_nowait()
                
                # Resize frame to fit the panel
                frame = self._resize_image_for_display(frame)
                
                # Convert to PhotoImage
                img = Image.fromarray(frame)
                img_tk = ImageTk.PhotoImage(image=img)
                
                # Update image panel
                self.image_panel.configure(image=img_tk)
                self.image_panel.image = img_tk  # Keep a reference
                
                # Store current image
                self.current_image = frame
            
            # Schedule next update
            self.root.after(30, self._update_camera_feed)
            
        except Exception as e:
            logger.error(f"Error updating camera feed: {str(e)}")
            self.camera_active = False
    
    def _capture_image(self):
        """Capture the current camera frame"""
        if not self.camera_active or self.current_image is None:
            self._set_status("Camera not active or no image available")
            return
        
        try:
            # Create a copy of the current image
            captured_image = self.current_image.copy()
            
            # Save the image to a temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "images")
            os.makedirs(image_dir, exist_ok=True)
            
            image_path = os.path.join(image_dir, f"capture_{timestamp}.jpg")
            
            # Convert RGB to BGR for saving
            cv2.imwrite(image_path, cv2.cvtColor(captured_image, cv2.COLOR_RGB2BGR))
            
            # Update current image path
            self.current_image_path = image_path
            
            self._set_status(f"Image captured and saved to {image_path}")
            
        except Exception as e:
            error_msg = f"Error capturing image: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Capture Error", error_msg)
    
    def _load_image(self):
        """Load an image from file"""
        try:
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
            )
            
            if not file_path:
                return  # User cancelled
            
            # Load the image
            image = cv2.imread(file_path)
            
            if image is None:
                raise Exception("Failed to load image")
            
            # Convert to RGB for display
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize for display
            image_resized = self._resize_image_for_display(image_rgb)
            
            # Convert to PhotoImage
            img = Image.fromarray(image_resized)
            img_tk = ImageTk.PhotoImage(image=img)
            
            # Update image panel
            self.image_panel.configure(image=img_tk)
            self.image_panel.image = img_tk  # Keep a reference
            
            # Store current image and path
            self.current_image = image_rgb
            self.current_image_path = file_path
            
            self._set_status(f"Image loaded from {file_path}")
            
        except Exception as e:
            error_msg = f"Error loading image: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Load Error", error_msg)
    
    def _resize_image_for_display(self, image, max_width=800, max_height=600):
        """Resize image for display while maintaining aspect ratio
        
        Args:
            image (numpy.ndarray): Input image
            max_width (int): Maximum width
            max_height (int): Maximum height
            
        Returns:
            numpy.ndarray: Resized image
        """
        # Get original dimensions
        height, width = image.shape[:2]
        
        # Calculate aspect ratio
        aspect_ratio = width / height
        
        # Calculate new dimensions
        if width > max_width or height > max_height:
            if aspect_ratio > 1:  # Width > Height
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
            else:  # Height >= Width
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
        else:
            # Image is already smaller than max dimensions
            return image
        
        # Resize image
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return resized_image
    
    def _classify_image(self):
        """Classify the current image"""
        if self.current_image is None or self.current_image_path is None:
            self._set_status("No image available for classification")
            messagebox.showwarning("Classification Error", "Please capture or load an image first")
            return
        
        # Get animal ID and breed
        animal_id = self.animal_id_var.get().strip()
        breed = self.breed_var.get()
        
        if not animal_id:
            self._set_status("Animal ID is required")
            messagebox.showwarning("Classification Error", "Please enter an Animal ID")
            return
        
        if not breed:
            self._set_status("Breed is required")
            messagebox.showwarning("Classification Error", "Please select a Breed")
            return
        
        try:
            # Show processing status
            self._set_status("Processing image...")
            self.root.update()
            
            # Process the image and classify
            self.current_animal_id = animal_id
            self.current_breed = breed
            
            # Call the system's classification function
            # First, extract features from the image
            features = self.system.process_image(self.current_image_path)
            if features is None:
                raise Exception("Feature extraction failed")
            # Then, classify using the features
            classification_result = self.system.classify_animal(features)
            
            if classification_result is None:
                raise Exception("Classification failed")
            
            # Store the classification result
            self.current_classification = classification_result
            
            # Update the UI with results
            self._update_results_display(classification_result)
            
            self._set_status("Classification completed successfully")
            
        except Exception as e:
            error_msg = f"Error classifying image: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Classification Error", error_msg)
    
    def _update_results_display(self, classification_result):
        """Update the UI with classification results
        
        Args:
            classification_result (dict): Classification results
        """
        # Update overall score and classification
        overall_score = classification_result.get('overall_score', 0)
        classification = classification_result.get('classification', 'Unknown')
        
        self.overall_score_label.config(text=f"{overall_score:.1f}")
        self.classification_label.config(text=classification.replace('_', ' ').title())
        
        # Update trait scores
        trait_scores = classification_result.get('trait_scores', {})
        for trait, label in self.score_labels.items():
            score = trait_scores.get(trait, '-')
            if isinstance(score, (int, float)):
                label.config(text=f"{score:.1f}")
            else:
                label.config(text=str(score))
        
        # Update measurements
        measurements = classification_result.get('measurements', {})
        for trait, label in self.measurement_labels.items():
            value = measurements.get(trait, '-')
            if isinstance(value, (int, float)):
                label.config(text=f"{value:.2f}")
            else:
                label.config(text=str(value))
    
    def _save_results(self):
        """Save the classification results"""
        if self.current_classification is None:
            self._set_status("No classification results to save")
            messagebox.showwarning("Save Error", "Please classify an image first")
            return
        
        try:
            # Extract required fields from current_classification
            classification = self.current_classification
            animal_id = classification.get('animal_id')
            features = classification.get('measurements', {})
            scores = classification.get('trait_scores', {})
            # Save classification to database
            classification_id = self.system.save_classification(animal_id, features, scores)
            if classification_id:
                self._set_status(f"Classification saved with ID: {classification_id}")
                messagebox.showinfo("Save Successful", f"Classification saved with ID: {classification_id}")
            else:
                raise Exception("Failed to save classification")
        except Exception as e:
            error_msg = f"Error saving results: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Save Error", error_msg)
    
    def _sync_with_bpa(self):
        """Sync the current classification with BPA"""
        if self.current_classification is None:
            self._set_status("No classification results to sync")
            messagebox.showwarning("Sync Error", "Please classify an image first")
            return
        
        try:
            # Check if classification is saved
            if 'id' not in self.current_classification:
                # Save classification first
                classification = self.current_classification
                animal_id = classification.get('animal_id')
                features = classification.get('measurements', {})
                scores = classification.get('trait_scores', {})
                classification_id = self.system.save_classification(animal_id, features, scores)
                if not classification_id:
                    raise Exception("Failed to save classification before sync")
                # Update the classification with the ID
                self.current_classification['id'] = classification_id
            
            # Show syncing status
            self._set_status("Syncing with BPA...")
            self.root.update()
            
            # Sync with BPA
            classification = self.current_classification
            animal_id = classification.get('animal_id')
            scores = classification.get('trait_scores', {})
            sync_result = self.system.sync_with_bpa(animal_id, scores)
            
            if sync_result.get('success', False):
                self._set_status("Sync with BPA completed successfully")
                messagebox.showinfo("Sync Successful", "Classification synced with BPA successfully")
            else:
                error_msg = sync_result.get('message', "Unknown error")
                raise Exception(f"Sync failed: {error_msg}")
            
        except Exception as e:
            error_msg = f"Error syncing with BPA: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Sync Error", error_msg)
    
    def _search_animal(self):
        """Search for an animal by ID"""
        animal_id = self.animal_id_var.get().strip()
        
        if not animal_id:
            self._set_status("Animal ID is required for search")
            messagebox.showwarning("Search Error", "Please enter an Animal ID")
            return
        
        try:
            # Search for animal in database
            animal_info = self.system.get_animal_info(animal_id)
            
            if animal_info:
                # Update breed if available
                if 'breed' in animal_info and animal_info['breed']:
                    self.breed_var.set(animal_info['breed'].title())
                
                # Show animal info
                info_str = f"Found animal: {animal_id}\n"
                for key, value in animal_info.items():
                    if key != 'animal_id' and value:
                        info_str += f"{key.replace('_', ' ').title()}: {value}\n"
                
                self._set_status(f"Animal found: {animal_id}")
                messagebox.showinfo("Animal Information", info_str)
            else:
                self._set_status(f"Animal not found: {animal_id}")
                messagebox.showinfo("Animal Not Found", f"No information found for animal ID: {animal_id}")
            
        except Exception as e:
            error_msg = f"Error searching for animal: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Search Error", error_msg)
    
    def _clear_all(self):
        """Clear all current data and results"""
        # Clear animal info
        self.animal_id_var.set("")
        self.breed_var.set("Gir")  # Reset to default
        
        # Clear image
        self.image_panel.configure(image=None)
        self.image_panel.image = None
        self.current_image = None
        self.current_image_path = None
        
        # Clear classification results
        self.current_classification = None
        self.overall_score_label.config(text="-")
        self.classification_label.config(text="-")
        
        # Clear trait scores and measurements
        for label in self.score_labels.values():
            label.config(text="-")
        
        for label in self.measurement_labels.values():
            label.config(text="-")
        
        self._set_status("All data cleared")
    
    def _set_status(self, message):
        """Set the status bar message
        
        Args:
            message (str): Status message
        """
        self.status_label.config(text=message)
        logger.info(message)
    
    def _on_close(self):
        """Handle window close event"""
        # Stop camera if active
        if self.camera_active:
            self.camera_active = False
            if self.camera_thread and self.camera_thread.is_alive():
                self.camera_thread.join(1.0)  # Wait for thread to finish
        
        # Close the window
        self.root.destroy()
        logger.info("User interface closed")


class BatchProcessingUI:
    """User interface for batch processing of images"""
    
    def __init__(self, system):
        """Initialize the batch processing UI
        
        Args:
            system: ATCSystem instance
        """
        self.system = system
        self.root = None
        self.image_folder = None
        self.output_folder = None
        self.default_breed = None
        self.processing_queue = []
        self.current_index = 0
        
        # UI components
        self.image_panel = None
        self.status_label = None
        self.progress_bar = None
        self.file_listbox = None
        
        logger.info("Batch processing UI initialized")
    
    def start(self):
        """Start the batch processing UI"""
        logger.info("Starting batch processing UI")
        
        # Create main window
        self.root = tk.Toplevel()
        self.root.title("Batch Processing - Animal Type Classification")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set up the UI layout
        self._setup_ui()
        
        # Start the main loop
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.grab_set()  # Make this window modal
        self.root.wait_window()
    
    def _setup_ui(self):
        """Set up the batch processing UI layout"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create top frame for folder selection
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        # Input folder selection
        ttk.Label(top_frame, text="Input Folder:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.input_folder_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.input_folder_var, width=50).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(top_frame, text="Browse", command=self._select_input_folder).grid(row=0, column=2, padx=5, pady=5)
        
        # Output folder selection
        ttk.Label(top_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_folder_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.output_folder_var, width=50).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(top_frame, text="Browse", command=self._select_output_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # Default breed selection
        ttk.Label(top_frame, text="Default Breed:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.default_breed_var = tk.StringVar()
        breeds = ["Gir", "Sahiwal", "Murrah", "Other"]  # Example breeds
        breed_combo = ttk.Combobox(top_frame, textvariable=self.default_breed_var, values=breeds, width=20)
        breed_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        breed_combo.current(0)  # Set default selection
        
        # Create middle frame with file list and image preview
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # File list on the left
        file_frame = ttk.LabelFrame(middle_frame, text="Image Files")
        file_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create listbox with scrollbar
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED)
        file_scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)
        
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.file_listbox.bind('<<ListboxSelect>>', self._on_file_select)
        
        # Image preview on the right
        preview_frame = ttk.LabelFrame(middle_frame, text="Preview")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Create a canvas for the image
        preview_canvas = tk.Canvas(preview_frame, bg="black")
        preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder for image panel
        self.image_panel = ttk.Label(preview_canvas)
        preview_canvas.create_window(0, 0, anchor=tk.NW, window=self.image_panel)
        
        # Create bottom frame for action buttons and progress
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        # Action buttons
        ttk.Button(bottom_frame, text="Load Files", command=self._load_files).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(bottom_frame, text="Process Selected", command=self._process_selected).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(bottom_frame, text="Process All", command=self._process_all).grid(row=0, column=2, padx=5, pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(bottom_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress_bar.grid(row=0, column=3, padx=10, pady=5, sticky=tk.E)
        
        # Status bar at the bottom
        self.status_label = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _select_input_folder(self):
        """Select input folder for batch processing"""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder_var.set(folder)
            self.image_folder = folder
    
    def _select_output_folder(self):
        """Select output folder for results"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)
            self.output_folder = folder
    
    def _load_files(self):
        """Load image files from the selected folder"""
        folder = self.input_folder_var.get()
        
        if not folder or not os.path.isdir(folder):
            self._set_status("Please select a valid input folder")
            messagebox.showwarning("Folder Error", "Please select a valid input folder")
            return
        
        try:
            # Clear current list
            self.file_listbox.delete(0, tk.END)
            
            # Find image files
            image_extensions = (".jpg", ".jpeg", ".png", ".bmp")
            image_files = [f for f in os.listdir(folder) if f.lower().endswith(image_extensions)]
            
            if not image_files:
                self._set_status("No image files found in the selected folder")
                messagebox.showinfo("No Files", "No image files found in the selected folder")
                return
            
            # Add files to listbox
            for file in sorted(image_files):
                self.file_listbox.insert(tk.END, file)
            
            self._set_status(f"Loaded {len(image_files)} image files")
            
        except Exception as e:
            error_msg = f"Error loading files: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            messagebox.showerror("Load Error", error_msg)
    
    def _on_file_select(self, event):
        """Handle file selection in listbox"""
        selection = self.file_listbox.curselection()
        
        if not selection:
            return
        
        # Get the selected file
        index = selection[0]
        filename = self.file_listbox.get(index)
        
        # Load and display the image
        try:
            file_path = os.path.join(self.input_folder_var.get(), filename)
            
            # Load the image
            image = cv2.imread(file_path)
            
            if image is None:
                raise Exception("Failed to load image")
            
            # Convert to RGB for display
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize for display
            image_resized = cv2.resize(image_rgb, (400, 300), interpolation=cv2.INTER_AREA)
            
            # Convert to PhotoImage
            img = Image.fromarray(image_resized)
            img_tk = ImageTk.PhotoImage(image=img)
            
            # Update image panel
            self.image_panel.configure(image=img_tk)
            self.image_panel.image = img_tk  # Keep a reference
            
            self._set_status(f"Previewing: {filename}")
            
        except Exception as e:
            logger.error(f"Error previewing image: {str(e)}")
    
    def _process_selected(self):
        """Process selected image files"""
        selection = self.file_listbox.curselection()
        
        if not selection:
            self._set_status("No files selected")
            messagebox.showwarning("Selection Error", "Please select files to process")
            return
        
        # Get selected files
        selected_files = [self.file_listbox.get(i) for i in selection]
        
        # Check output folder
        if not self._check_folders():
            return
        
        # Get default breed
        default_breed = self.default_breed_var.get()
        
        # Prepare processing queue
        self.processing_queue = []
        for filename in selected_files:
            file_path = os.path.join(self.image_folder, filename)
            self.processing_queue.append((file_path, filename))
        
        # Start processing
        self._start_batch_processing(default_breed)
    
    def _process_all(self):
        """Process all image files in the folder"""
        # Check if files are loaded
        if self.file_listbox.size() == 0:
            self._set_status("No files loaded")
            messagebox.showwarning("File Error", "Please load files first")
            return
        
        # Check output folder
        if not self._check_folders():
            return
        
        # Get default breed
        default_breed = self.default_breed_var.get()
        
        # Prepare processing queue
        self.processing_queue = []
        for i in range(self.file_listbox.size()):
            filename = self.file_listbox.get(i)
            file_path = os.path.join(self.image_folder, filename)
            self.processing_queue.append((file_path, filename))
        
        # Start processing
        self._start_batch_processing(default_breed)
    
    def _check_folders(self):
        """Check if input and output folders are valid
        
        Returns:
            bool: True if valid, False otherwise
        """
        # Check input folder
        input_folder = self.input_folder_var.get()
        if not input_folder or not os.path.isdir(input_folder):
            self._set_status("Invalid input folder")
            messagebox.showwarning("Folder Error", "Please select a valid input folder")
            return False
        
        # Check output folder
        output_folder = self.output_folder_var.get()
        if not output_folder:
            self._set_status("Output folder not specified")
            messagebox.showwarning("Folder Error", "Please select an output folder")
            return False
        
        # Create output folder if it doesn't exist
        try:
            os.makedirs(output_folder, exist_ok=True)
        except Exception as e:
            self._set_status(f"Error creating output folder: {str(e)}")
            messagebox.showerror("Folder Error", f"Error creating output folder: {str(e)}")
            return False
        
        return True
    
    def _start_batch_processing(self, default_breed):
        """Start batch processing of images
        
        Args:
            default_breed (str): Default breed to use
        """
        if not self.processing_queue:
            self._set_status("No files to process")
            return
        
        # Reset progress
        self.current_index = 0
        self.progress_bar['maximum'] = len(self.processing_queue)
        self.progress_bar['value'] = 0
        
        # Start processing
        self._process_next_image(default_breed)
    
    def _process_next_image(self, default_breed):
        """Process the next image in the queue
        
        Args:
            default_breed (str): Default breed to use
        """
        if self.current_index >= len(self.processing_queue):
            # All done
            self._set_status(f"Batch processing completed: {self.current_index} images processed")
            messagebox.showinfo("Processing Complete", f"Processed {self.current_index} images successfully")
            return
        
        # Get next file
        file_path, filename = self.processing_queue[self.current_index]
        
        try:
            # Update status
            self._set_status(f"Processing {self.current_index + 1}/{len(self.processing_queue)}: {filename}")
            self.root.update()
            
            # Generate a unique animal ID for this image
            animal_id = f"BATCH-{datetime.now().strftime('%Y%m%d')}-{self.current_index + 1}"
            
            # Process the image
            # First, extract features from the image
            features = self.system.process_image(file_path)
            if features is None:
                raise Exception("Feature extraction failed")
            # Then, classify using the features
            result = self.system.classify_animal(features)
            
            if result is None:
                raise Exception("Classification failed")
            
            # Save results to output folder
            output_file = os.path.join(self.output_folder, f"{os.path.splitext(filename)[0]}_result.json")
            
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Update progress
            self.current_index += 1
            self.progress_bar['value'] = self.current_index
            
            # Process next image
            self.root.after(100, lambda: self._process_next_image(default_breed))
            
        except Exception as e:
            error_msg = f"Error processing {filename}: {str(e)}"
            logger.error(error_msg)
            self._set_status(error_msg)
            
            # Ask whether to continue
            if messagebox.askyesno("Processing Error", f"Error processing {filename}. Continue with next image?"):
                self.current_index += 1
                self.progress_bar['value'] = self.current_index
                self.root.after(100, lambda: self._process_next_image(default_breed))
            else:
                self._set_status("Batch processing stopped")
    
    def _set_status(self, message):
        """Set the status bar message
        
        Args:
            message (str): Status message
        """
        self.status_label.config(text=message)
        logger.info(message)
    
    def _on_close(self):
        """Handle window close event"""
        # Close the window
        self.root.destroy()
        logger.info("Batch processing UI closed")