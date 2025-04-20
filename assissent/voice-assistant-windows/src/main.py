"""
Main Voice Assistant Application

This module integrates the voice recognition, command processing, and response generation
modules to create a complete voice assistant system.
"""

import os
import sys
import time
import logging
import threading
import argparse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('voice_assistant')

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules
from src.voice_recognition import VoiceRecognitionModule
from src.command_processing import CommandProcessor
from src.response_generation import ResponseGenerationModule


class VoiceAssistant:
    """Main voice assistant class that integrates all modules."""
    
    def __init__(self, config_file=None):
        """
        Initialize the voice assistant.
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.running = False
        self.setup_complete = False
        
        # Initialize modules
        self._setup_modules()
        
        # Set up callbacks
        self._setup_callbacks()
        
        self.setup_complete = True
        logger.info("Voice assistant initialization complete")
    
    def _load_config(self, config_file):
        """
        Load configuration from file or use defaults.
        
        Args:
            config_file (str): Path to configuration file
            
        Returns:
            dict: Configuration settings
        """
        default_config = {
            "assistant_name": "jarvis",
            "wake_words": ["jarvis", "hey jarvis"],
            "voice_recognition": {
                "vosk_model_path": None,  # Will use default path
                "whisper_model_name": "base",
                "sample_rate": 160,
                "chunk_size": 1024,
                "sensitivity": 0.6
            },
            "command_processing": {
                "custom_skills_dir": None
            },
            "response_generation": {
                "templates_file": None,
                "sound_effects_dir": None,
                "voice": None,  # Will use default voice
                "rate": 200,
                "volume": 1.0
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                
                # Merge user config with defaults
                for section in user_config:
                    if section in default_config and isinstance(default_config[section], dict):
                        default_config[section].update(user_config[section])
                    else:
                        default_config[section] = user_config[section]
                
                logger.info(f"Loaded configuration from {config_file}")
            
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        return default_config
    
    def _setup_modules(self):
        """Set up the voice assistant modules."""
        # Voice Recognition Module
        vr_config = self.config["voice_recognition"]
        self.voice_recognition = VoiceRecognitionModule(
            wake_words=self.config["wake_words"],
            vosk_model_path=vr_config["vosk_model_path"],
            whisper_model_name=vr_config["whisper_model_name"],
            sample_rate=vr_config["sample_rate"],
            chunk_size=vr_config["chunk_size"],
            sensitivity=vr_config["sensitivity"]
        )
        
        # Command Processing Module
        cp_config = self.config["command_processing"]
        self.command_processor = CommandProcessor(
            custom_skills_dir=cp_config["custom_skills_dir"]
        )
        
        # Response Generation Module
        rg_config = self.config["response_generation"]
        self.response_generator = ResponseGenerationModule(
            templates_file=rg_config["templates_file"],
            sound_effects_dir=rg_config["sound_effects_dir"],
            voice=rg_config["voice"],
            rate=rg_config["rate"],
            volume=rg_config["volume"]
        )
    
    def _setup_callbacks(self):
        """Set up callbacks between modules."""
        # Voice Recognition callbacks
        self.voice_recognition.on_wake_word = self._on_wake_word
        self.voice_recognition.on_command = self._on_command
        self.voice_recognition.on_timeout = self._on_timeout
        self.voice_recognition.on_error = self._on_error
        
        # Response Generation callbacks
        self.response_generator.on_response_start = self._on_response_start
        self.response_generator.on_response_complete = self._on_response_complete
    
    def start(self):
        """Start the voice assistant."""
        if self.running:
            logger.warning("Voice assistant is already running")
            return False
        
        if not self.setup_complete:
            logger.error("Voice assistant setup is not complete")
            return False
        
        # Start the voice recognition module
        if not self.voice_recognition.start():
            logger.error("Failed to start voice recognition module")
            return False
        
        self.running = True
        logger.info("Voice assistant started")
        
        # Speak a startup message
        self.response_generator.speak_text(f"Hello, I'm {self.config['assistant_name']}. How can I help you?")
        
        return True
    
    def stop(self):
        """Stop the voice assistant."""
        if not self.running:
            logger.warning("Voice assistant is not running")
            return False
        
        # Stop the voice recognition module
        self.voice_recognition.stop()
        
        self.running = False
        logger.info("Voice assistant stopped")
        
        # Speak a shutdown message
        self.response_generator.speak_text("Goodbye!")
        
        return True
    
    def _on_wake_word(self):
        """Handle wake word detection."""
        logger.info("Wake word detected")
        
        # Play wake sound
        self.response_generator.play_wake_sound()
        
        # Optionally speak a prompt
        # self.response_generator.speak_text("Yes?")
    
    def _on_command(self, recognition_result):
        """
        Handle command recognition.
        
        Args:
            recognition_result (dict): Recognition result from voice recognition module
        """
        text = recognition_result["text"]
        logger.info(f"Command recognized: {text}")
        
        # Play listening sound
        self.response_generator.play_listening_sound()
        
        # Process the command
        command_result = self.command_processor.process_command(text)
        
        # Generate and deliver response
        self.response_generator.generate_response(command_result)
        
        # Handle special actions
        if command_result.get("success", False):
            action = command_result.get("data", {}).get("action", None)
            
            if action == "stop":
                # Stop the assistant
                self.stop()
    
    def _on_timeout(self):
        """Handle command timeout."""
        logger.info("Command timeout")
        
        # Generate a timeout response
        timeout_result = {
            "intent": "timeout",
            "success": False,
            "message": "I didn't hear a command. Please try again.",
            "data": {}
        }
        
        self.response_generator.generate_response(timeout_result)
    
    def _on_error(self, error):
        """
        Handle errors.
        
        Args:
            error (str): Error message
        """
        logger.error(f"Error: {error}")
        
        # Generate an error response
        error_result = {
            "intent": "error",
            "success": False,
            "message": f"Sorry, there was an error: {error}",
            "data": {}
        }
        
        self.response_generator.generate_response(error_result)
    
    def _on_response_start(self, response):
        """
        Handle response start.
        
        Args:
            response (dict): Response data
        """
        logger.debug(f"Response started: {response['text']}")
    
    def _on_response_complete(self, response):
        """
        Handle response complete.
        
        Args:
            response (dict): Response data
        """
        logger.debug("Response complete")
    
    def set_wake_words(self, wake_words):
        """
        Set new wake words.
        
        Args:
            wake_words (list): List of wake word phrases
        """
        self.config["wake_words"] = wake_words
        self.voice_recognition.set_wake_words(wake_words)
        logger.info(f"Wake words updated: {wake_words}")
    
    def set_voice(self, voice):
        """
        Set the TTS voice.
        
        Args:
            voice (str): Voice name
        """
        result = self.response_generator.set_voice(voice)
        if result:
            self.config["response_generation"]["voice"] = voice
        return result
    
    def set_sensitivity(self, sensitivity):
        """
        Set wake word detection sensitivity.
        
        Args:
            sensitivity (float): Detection sensitivity (0.0-1.0)
        """
        self.config["voice_recognition"]["sensitivity"] = sensitivity
        self.voice_recognition.set_sensitivity(sensitivity)
        logger.info(f"Sensitivity updated: {sensitivity}")
    
    def save_config(self, config_file):
        """
        Save current configuration to file.
        
        Args:
            config_file (str): Path to save configuration
        """
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False


def main():
    """Main function to run the voice assistant."""
    parser = argparse.ArgumentParser(description="Personal Voice Assistant")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create and start the voice assistant
    assistant = VoiceAssistant(config_file=args.config)
    assistant.start()
    
    try:
        # Keep the program running
        print("Voice assistant is running. Press Ctrl+C to stop.")
        while assistant.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping voice assistant...")
    finally:
        assistant.stop()


if __name__ == "__main__":
    main()
