#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Animal Type Classification System Runner

This script serves as the entry point for the Animal Type Classification System.
It initializes the system and starts the user interface.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Ensure the modules directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main system class
from main import ATCSystem

def setup_logging(log_level="INFO"):
    """Set up logging configuration
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"atc_system_{timestamp}.log")
    
    # Configure logging
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def parse_arguments():
    """Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Animal Type Classification System")
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--batch", 
        action="store_true",
        help="Start in batch processing mode"
    )
    
    parser.add_argument(
        "--input-dir", 
        type=str,
        help="Input directory for batch processing"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str,
        help="Output directory for batch processing results"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Starting Animal Type Classification System")
    
    try:
        # Initialize the system
        system = ATCSystem(config_path=args.config)
        
        # Start the system
        if args.batch:
            # Batch processing mode
            if not args.input_dir:
                logger.error("Input directory must be specified for batch mode")
                print("Error: Input directory must be specified for batch mode")
                return 1
            
            if not args.output_dir:
                logger.error("Output directory must be specified for batch mode")
                print("Error: Output directory must be specified for batch mode")
                return 1
            
            logger.info(f"Starting batch processing: {args.input_dir} -> {args.output_dir}")
            system.run_batch(args.input_dir, args.output_dir)
        else:
            # Interactive UI mode
            logger.info("Starting interactive mode")
            system.run()
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error running the system: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())