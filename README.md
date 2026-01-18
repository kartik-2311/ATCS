# AI-based Animal Type Classification System

## Overview

This system automates the Animal Type Classification (ATC) process for dairy farming under the Rashtriya Gokul Mission (RGM). It uses artificial intelligence and image processing to evaluate the body structure of cattle and buffaloes, generating standardized scores for physical traits that are crucial for identifying elite dams for breeding programs.

## Features

- **Automated Image Analysis**: Processes images of cattle and buffaloes to extract body structure parameters
- **AI-Powered Measurements**: Uses computer vision to measure key physical traits (body length, height, chest width, etc.)
- **Standardized Scoring**: Generates objective classification scores based on breed standards
- **Database Integration**: Stores all classification data in a structured format
- **Bharat Pashudhan App (BPA) Integration**: Seamlessly syncs classification records with the BPA
- **User-Friendly Interface**: Simple interface designed for field personnel with minimal technical skills
- **Batch Processing**: Supports processing multiple images in a single operation

## System Requirements

- Python 3.7 or higher
- Camera (for live capture) or image files
- Internet connection (for BPA synchronization)

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the system settings in `config.json` (will be created on first run)

## Usage

### Starting the Application

Run the main application:

```bash
python main.py
```

### Basic Workflow

1. **Capture or Load Image**: Use the camera to capture a new image or load an existing one
2. **Enter Animal Information**: Provide the animal ID and select the breed
3. **Classify**: Process the image to extract measurements and generate scores
4. **Review Results**: Examine the classification scores and measurements
5. **Save and Sync**: Save the results locally and optionally sync with the BPA

### Batch Processing

For processing multiple images:

1. Select "Batch Processing" from the menu
2. Choose the input folder containing images
3. Select an output folder for results
4. Set the default breed for classification
5. Click "Process All" or select specific images to process

## Modules

- **Image Processing**: Handles image capture, preprocessing, and feature extraction
- **AI Model**: Detects keypoints and calculates body measurements
- **Scoring**: Converts measurements to standardized scores based on breed standards
- **Database**: Manages local storage of classification data
- **BPA Integration**: Handles synchronization with the Bharat Pashudhan App
- **User Interface**: Provides an intuitive interface for field personnel

## Configuration

The system can be configured through the `config.json` file or through the settings interface in the application. Key configuration options include:

- Camera settings
- Breed standards and scoring parameters
- BPA API connection details
- Database location

## Troubleshooting

- **Camera Issues**: Ensure your camera is properly connected and not in use by another application
- **Classification Errors**: Check that the animal is properly positioned in the image
- **Sync Failures**: Verify your internet connection and BPA credentials

## License

This software is developed for the Government of India's Rashtriya Gokul Mission (RGM) program.

## Contact

For support or inquiries, please contact the development team.