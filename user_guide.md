# Animal Type Classification System - User Guide

## Introduction

The Animal Type Classification (ATC) System is designed to help field personnel evaluate the body structure of cattle and buffaloes using AI technology. This guide will help you get started with the system and understand its features.

## Getting Started

### Installation

1. Ensure you have Python 3.7 or higher installed on your computer
2. Install the required dependencies by running: `pip install -r requirements.txt`
3. Run the application: `python run.py`

### First-Time Setup

When you first run the application, you'll need to:

1. Configure your camera (if using live capture)
2. Set up your Bharat Pashudhan App (BPA) credentials (if syncing data)

## Main Interface

![Main Interface](images/main_interface.png)

### Interface Components

1. **Animal Information Panel**: Enter animal ID and select breed
2. **Camera Controls**: Start camera, capture image, or load existing image
3. **Image Display**: Shows the current animal image
4. **Classification Results**: Displays scores and measurements
5. **Action Buttons**: Classify, Save, Sync, and Clear
6. **Status Bar**: Shows current system status

## Basic Workflow

### Step 1: Capture or Load an Image

**Option A: Capture a new image**
- Position the animal correctly (side view is recommended)
- Click "Start Camera" to activate your camera
- Click "Capture" when the animal is properly positioned

**Option B: Load an existing image**
- Click "Load Image"
- Browse to select an image file

### Step 2: Enter Animal Information

- Enter the Animal ID in the provided field
- Select the appropriate breed from the dropdown menu
- Click "Search" to retrieve existing information (if available)

### Step 3: Classify the Animal

- Click the "Classify" button
- The system will process the image and extract measurements
- Classification scores will be displayed in the results panel

### Step 4: Review Results

- Check the overall score and classification
- Review individual trait scores
- Examine the measurements extracted from the image

### Step 5: Save and Sync

- Click "Save Results" to store the classification in the local database
- Click "Sync with BPA" to upload the results to the Bharat Pashudhan App

## Batch Processing

For processing multiple images at once:

1. Click on "File" > "Batch Processing" in the menu
2. In the batch processing window:
   - Select the input folder containing images
   - Choose an output folder for results
   - Set the default breed
   - Click "Load Files" to see available images
   - Select images to process or click "Process All"

## Tips for Best Results

### Image Capture

- Ensure good lighting conditions
- Position the animal against a contrasting background
- Capture a clear side view of the animal
- Keep the animal standing straight with legs visible
- Avoid shadows across the animal's body

### Measurements

For accurate measurements, the system needs to identify these key points:

- Head
- Withers (highest point of the shoulder)
- Back
- Tail head
- Hip
- Chest
- Legs

## Troubleshooting

### Camera Issues

- **Camera not starting**: Check if another application is using the camera
- **Poor image quality**: Adjust lighting or camera settings

### Classification Issues

- **Low confidence scores**: Improve image quality or animal positioning
- **Missing measurements**: Ensure all body parts are visible in the image

### Sync Issues

- **Connection errors**: Check your internet connection
- **Authentication failures**: Verify your BPA credentials

## Support

If you encounter any issues not covered in this guide, please contact technical support.

---

*This user guide is for the AI-based Animal Type Classification System developed for the Rashtriya Gokul Mission (RGM) program.*
.\.venv\Scripts\python.exe c:\KARTIK\run.py