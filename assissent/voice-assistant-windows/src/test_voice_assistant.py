"""
Test script for the voice assistant.
This script tests the functionality of the integrated voice assistant system.
"""

import os
import sys
import time
import unittest
import threading
import tempfile
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_voice_assistant')

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules
from src.voice_recognition import VoiceRecognitionModule, AudioInputHandler
from src.command_processing import CommandProcessor, IntentParser
from src.response_generation import ResponseGenerationModule, ResponseFormatter
from src.main import VoiceAssistant


class TestVoiceRecognition(unittest.TestCase):
    """Test the voice recognition module."""
    
    def test_audio_input_handler_init(self):
        """Test AudioInputHandler initialization."""
        handler = AudioInputHandler()
        self.assertIsNotNone(handler)
        self.assertEqual(handler.sample_rate, 16000)
        self.assertEqual(handler.chunk_size, 1024)
        self.assertFalse(handler.is_listening)
    
    def test_wake_word_detector_init(self):
        """Test WakeWordDetector initialization."""
        from src.voice_recognition import WakeWordDetector
        detector = WakeWordDetector(wake_words=["test wake word"])
        self.assertIsNotNone(detector)
        self.assertEqual(detector.wake_words, ["test wake word"])
        self.assertEqual(detector.sensitivity, 0.5)
    
    def test_speech_recognizer_init(self):
        """Test SpeechRecognizer initialization."""
        from src.voice_recognition import SpeechRecognizer
        recognizer = SpeechRecognizer(whisper_model_name="tiny")
        self.assertIsNotNone(recognizer)
        self.assertEqual(recognizer.whisper_model_name, "tiny")
    
    def test_voice_recognition_module_init(self):
        """Test VoiceRecognitionModule initialization."""
        module = VoiceRecognitionModule(wake_words=["test wake word"])
        self.assertIsNotNone(module)
        self.assertEqual(module.wake_detector.wake_words, ["test wake word"])
        self.assertFalse(module.is_running)


class TestCommandProcessing(unittest.TestCase):
    """Test the command processing module."""
    
    def test_intent_parser(self):
        """Test IntentParser functionality."""
        parser = IntentParser()
        
        # Test time intent
        result = parser.parse("what time is it")
        self.assertEqual(result["intent"], "time")
        self.assertTrue(result["confidence"] > 0.5)
        
        # Test date intent
        result = parser.parse("what's the date today")
        self.assertEqual(result["intent"], "date")
        self.assertTrue(result["confidence"] > 0.5)
        
        # Test unknown intent
        result = parser.parse("blah blah random text")
        self.assertEqual(result["intent"], "unknown")
    
    def test_command_processor(self):
        """Test CommandProcessor functionality."""
        processor = CommandProcessor()
        
        # Test time command
        result = processor.process_command("what time is it")
        self.assertEqual(result["intent"], "time")
        self.assertTrue(result["success"])
        
        # Test help command
        result = processor.process_command("help me")
        self.assertEqual(result["intent"], "help")
        self.assertTrue(result["success"])
        
        # Test unknown command
        result = processor.process_command("do something impossible")
        self.assertEqual(result["intent"], "unknown")
        self.assertFalse(result["success"])


class TestResponseGeneration(unittest.TestCase):
    """Test the response generation module."""
    
    def test_response_formatter(self):
        """Test ResponseFormatter functionality."""
        formatter = ResponseFormatter()
        
        # Test time response
        result = formatter.format_response({
            "intent": "time",
            "success": True,
            "data": {"time": "3:30 PM"}
        })
        self.assertIn("3:30 PM", result)
        
        # Test error response
        result = formatter.format_response({
            "intent": "unknown",
            "success": False,
            "data": {}
        })
        self.assertIn("not sure", result.lower())
    
    def test_response_generation_module(self):
        """Test ResponseGenerationModule initialization."""
        module = ResponseGenerationModule()
        self.assertIsNotNone(module)
        
        # Test response generation
        response = module.generate_response({
            "intent": "time",
            "success": True,
            "data": {"time": "3:30 PM"}
        }, speak=False, sound=False)
        
        self.assertIn("text", response)
        self.assertIn("3:30 PM", response["text"])


class TestVoiceAssistant(unittest.TestCase):
    """Test the integrated voice assistant."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "config.json")
        
        config = {
            "assistant_name": "Test Assistant",
            "wake_words": ["test wake word"],
            "voice_recognition": {
                "whisper_model_name": "tiny",
                "sample_rate": 16000,
                "chunk_size": 1024,
                "sensitivity": 0.5
            },
            "command_processing": {
                "custom_skills_dir": None
            },
            "response_generation": {
                "voice": None,
                "rate": 200,
                "volume": 1.0
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
    
    def test_voice_assistant_init(self):
        """Test VoiceAssistant initialization."""
        assistant = VoiceAssistant(config_file=self.config_file)
        self.assertIsNotNone(assistant)
        self.assertEqual(assistant.config["assistant_name"], "Test Assistant")
        self.assertEqual(assistant.config["wake_words"], ["test wake word"])
        self.assertTrue(assistant.setup_complete)
        self.assertFalse(assistant.running)
    
    def test_command_flow(self):
        """Test the command processing flow."""
        assistant = VoiceAssistant(config_file=self.config_file)
        
        # Mock the voice recognition to simulate a command
        def simulate_command():
            # Wait a bit for the assistant to start
            time.sleep(0.5)
            
            # Simulate a command being recognized
            assistant.voice_recognition.on_command({
                "text": "what time is it",
                "engine": "test",
                "confidence": 0.9,
                "success": True
            })
            
            # Wait for processing
            time.sleep(0.5)
            
            # Stop the assistant
            assistant.stop()
        
        # Start the simulation in a separate thread
        thread = threading.Thread(target=simulate_command)
        thread.daemon = True
        thread.start()
        
        # Start the assistant
        assistant.start()
        
        # Wait for the thread to complete
        thread.join(timeout=3.0)
        
        # Check that the assistant is stopped
        self.assertFalse(assistant.running)
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir)


def run_tests():
    """Run all tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests()
