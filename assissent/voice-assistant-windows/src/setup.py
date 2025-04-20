"""
Installation and setup script for the voice assistant.
This script installs required dependencies and sets up the environment.
"""

import os
import sys
import subprocess
import argparse
import platform

def check_python_version():
    """Check if Python version is compatible."""
    required_version = (3, 9)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required.")
        print(f"Current version: {current_version[0]}.{current_version[1]}")
        return False
    
    return True

def install_dependencies(include_optional=True):
    """Install required dependencies."""
    print("Installing required dependencies...")
    
    # Core dependencies
    core_packages = [
        "SpeechRecognition",
        "PyAudio",
        "numpy",
        "pyttsx3"
    ]
    
    # Optional dependencies
    optional_packages = []
    
    if include_optional:
        optional_packages = [
            "vosk",
            "openai-whisper",
            "gtts",
            "nltk"
        ]
    
    # Install core packages
    for package in core_packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}. Please install it manually.")
            if package == "PyAudio":
                print_pyaudio_help()
    
    # Install optional packages
    if optional_packages:
        print("\nInstalling optional dependencies...")
        for package in optional_packages:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}. Some features may not work.")
                if package == "openai-whisper":
                    print("Note: Whisper requires ffmpeg to be installed on your system.")
    
    print("\nDependency installation complete.")

def print_pyaudio_help():
    """Print help for installing PyAudio on different platforms."""
    system = platform.system()
    
    print("\nPyAudio installation help:")
    
    if system == "Windows":
        print("For Windows:")
        print("  1. Try: pip install pipwin")
        print("  2. Then: pipwin install pyaudio")
    
    elif system == "Darwin":  # macOS
        print("For macOS:")
        print("  1. Install portaudio with Homebrew: brew install portaudio")
        print("  2. Then: pip install pyaudio")
    
    elif system == "Linux":
        print("For Linux (Debian/Ubuntu):")
        print("  1. Install portaudio development package:")
        print("     sudo apt-get install python3-dev portaudio19-dev")
        print("  2. Then: pip install pyaudio")
    
    print("\nFor more details, visit: https://people.csail.mit.edu/hubert/pyaudio/")

def create_config_file(config_path):
    """Create a default configuration file."""
    import json
    
    default_config = {
        "assistant_name": "Assistant",
        "wake_words": ["hey assistant", "okay computer"],
        "voice_recognition": {
            "vosk_model_path": None,
            "whisper_model_name": "base",
            "sample_rate": 16000,
            "chunk_size": 1024,
            "sensitivity": 0.5
        },
        "command_processing": {
            "custom_skills_dir": None
        },
        "response_generation": {
            "templates_file": None,
            "sound_effects_dir": None,
            "voice": None,
            "rate": 200,
            "volume": 1.0
        }
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created default configuration file at {config_path}")
        return True
    except Exception as e:
        print(f"Error creating configuration file: {e}")
        return False

def create_directory_structure(base_dir):
    """Create the directory structure for the voice assistant."""
    directories = [
        "models",
        "models/vosk",
        "config",
        "sounds",
        "custom_skills"
    ]
    
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

def download_vosk_model(model_dir):
    """Download a Vosk model for English."""
    import urllib.request
    import zipfile
    import shutil
    
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = os.path.join(model_dir, "vosk-model.zip")
    
    print(f"Downloading Vosk model from {model_url}...")
    print("This may take a while depending on your internet connection.")
    
    try:
        # Download the model
        urllib.request.urlretrieve(model_url, zip_path)
        
        # Extract the model
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
        
        # Remove the zip file
        os.remove(zip_path)
        
        print("Vosk model downloaded and extracted successfully.")
        return True
    except Exception as e:
        print(f"Error downloading Vosk model: {e}")
        return False

def main():
    """Main function to set up the voice assistant."""
    parser = argparse.ArgumentParser(description="Set up the voice assistant")
    parser.add_argument("--dir", default=os.path.expanduser("~/voice_assistant"),
                        help="Base directory for the voice assistant")
    parser.add_argument("--skip-optional", action="store_true",
                        help="Skip installation of optional dependencies")
    parser.add_argument("--download-vosk", action="store_true",
                        help="Download Vosk model for offline speech recognition")
    args = parser.parse_args()
    
    print("Voice Assistant Setup")
    print("====================")
    
    # Check Python version
    if not check_python_version():
        return
    
    # Create directory structure
    create_directory_structure(args.dir)
    
    # Create default configuration
    config_path = os.path.join(args.dir, "config", "config.json")
    create_config_file(config_path)
    
    # Install dependencies
    install_dependencies(not args.skip_optional)
    
    # Download Vosk model if requested
    if args.download_vosk:
        model_dir = os.path.join(args.dir, "models", "vosk")
        download_vosk_model(model_dir)
    
    print("\nSetup complete!")
    print(f"Voice assistant installed at: {args.dir}")
    print("\nTo start the voice assistant, run:")
    print(f"python {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')} --config {config_path}")

if __name__ == "__main__":
    main()
