#Helper functions for file operations, directory creation, and JSON handling.

import os
import json

def create_directory(directory):
    """Create a directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_file(file_path):
    """Read the content of a file and return it as a list of lines."""
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return []

def save_to_file(data, file_path):
    """Save data to a file in JSON format."""
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error saving to file: {e}")
