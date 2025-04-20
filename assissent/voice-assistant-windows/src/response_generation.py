"""
Response Generation Module for Personal Voice Assistant

This module creates and delivers responses to the user based on command processing results.
It includes response formatting, text-to-speech conversion, and output handling.
"""

import os
import json
import logging
import threading
import tempfile
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('response_generation')

class ResponseFormatter:
    """Formats responses based on command results."""
    
    def __init__(self, templates_file=None):
        """
        Initialize the response formatter.
        
        Args:
            templates_file (str): Path to JSON file with response templates
        """
        self.templates = {}
        if templates_file and os.path.exists(templates_file):
            self._load_templates(templates_file)
        else:
            self._load_default_templates()
    
    def _load_templates(self, templates_file):
        """
        Load response templates from a JSON file.
        
        Args:
            templates_file (str): Path to JSON file with templates
        """
        try:
            with open(templates_file, 'r') as f:
                self.templates = json.load(f)
            logger.info(f"Loaded response templates from {templates_file}")
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default response templates."""
        self.templates = {
            # Default responses for different intents
            "default": {
                "success": "I've completed that task.",
                "failure": "I'm sorry, I couldn't do that."
            },
            
            # System responses
            "help": {
                "success": "Here are some things you can ask me: {commands_list}"
            },
            "stop": {
                "success": "Goodbye! I'll be here if you need me."
            },
            "cancel": {
                "success": "Alright, I've cancelled that."
            },
            "unknown": {
                "failure": "I'm not sure how to help with that. Try asking for help to see what I can do."
            },
            
            # Time responses
            "time": {
                "success": "The current time is {time}."
            },
            "date": {
                "success": "Today is {date}."
            },
            
            # Timer responses
            "set_timer": {
                "success": "I've set a timer for {minutes} minutes and {seconds} seconds.",
                "failure": "I couldn't set that timer. Please try again."
            },
            "check_timer": {
                "success_running": "Your timer has {minutes} minutes and {seconds} seconds remaining.",
                "success_finished": "Your timer has finished.",
                "failure": "You don't have any active timers."
            },
            "set_alarm": {
                "success": "Alarm set for {time}.",
                "failure": "I couldn't set that alarm. Please try again."
            },
            
            # Error responses
            "error": {
                "general": "Sorry, something went wrong.",
                "not_understood": "I didn't quite catch that.",
                "not_implemented": "I can't do that yet."
            }
        }
        logger.info("Loaded default response templates")
    
    def format_response(self, command_result):
        """
        Format a response based on command result.
        
        Args:
            command_result (dict): Result from command processor
            
        Returns:
            str: Formatted response text
        """
        intent = command_result.get("intent", "unknown")
        success = command_result.get("success", False)
        message = command_result.get("message", "")
        data = command_result.get("data", {})
        
        # If a message is provided, use it directly
        if message:
            return self._fill_placeholders(message, data)
        
        # Otherwise, use templates
        intent_templates = self.templates.get(intent, self.templates["default"])
        
        if success:
            # Special case for check_timer with different statuses
            if intent == "check_timer" and "status" in data:
                if data["status"] == "running":
                    template = intent_templates.get("success_running", intent_templates.get("success", ""))
                else:
                    template = intent_templates.get("success_finished", intent_templates.get("success", ""))
            else:
                template = intent_templates.get("success", self.templates["default"]["success"])
        else:
            template = intent_templates.get("failure", self.templates["default"]["failure"])
        
        return self._fill_placeholders(template, data)
    
    def _fill_placeholders(self, template, data):
        """
        Fill placeholders in template with data.
        
        Args:
            template (str): Template string with placeholders
            data (dict): Data to fill placeholders
            
        Returns:
            str: Filled template
        """
        # Special handling for commands list
        if "{commands_list}" in template and "commands" in data:
            commands = data["commands"]
            commands_text = ", ".join([f"{cmd}" for cmd in commands])
            template = template.replace("{commands_list}", commands_text)
        
        # Fill other placeholders
        for key, value in data.items():
            placeholder = "{" + key + "}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))
        
        return template
    
    def add_template(self, intent, status, template):
        """
        Add a new response template.
        
        Args:
            intent (str): Intent name
            status (str): Status (success/failure)
            template (str): Response template
        """
        if intent not in self.templates:
            self.templates[intent] = {}
        
        self.templates[intent][status] = template
        logger.info(f"Added template for {intent}/{status}")
    
    def save_templates(self, templates_file):
        """
        Save templates to a JSON file.
        
        Args:
            templates_file (str): Path to save templates
        """
        try:
            with open(templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
            logger.info(f"Saved templates to {templates_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving templates: {e}")
            return False


class TextToSpeechEngine:
    """Converts text responses to speech."""
    
    def __init__(self, voice=None, rate=200, volume=1.0):
        """
        Initialize the TTS engine.
        
        Args:
            voice (str): Voice name to use
            rate (int): Speech rate (words per minute)
            volume (float): Volume level (0.0-1.0)
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.engine = None
        self._setup_tts()
    
    def _setup_tts(self):
        """Set up the text-to-speech engine."""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Set properties
            if self.voice:
                voices = self.engine.getProperty('voices')
                for v in voices:
                    if self.voice.lower() in v.name.lower():
                        self.engine.setProperty('voice', v.id)
                        break
            
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            logger.info("Initialized pyttsx3 TTS engine")
            
        except ImportError:
            logger.warning("pyttsx3 not installed. Using fallback TTS.")
            self.engine = None
            self._setup_fallback_tts()
    
    def _setup_fallback_tts(self):
        """Set up fallback TTS using gTTS if available."""
        try:
            import gtts
            self.gtts_available = True
            logger.info("Using gTTS as fallback TTS engine")
        except ImportError:
            self.gtts_available = False
            logger.warning("Neither pyttsx3 nor gTTS available. TTS functionality will be limited.")
    
    def speak(self, text, blocking=False):
        """
        Convert text to speech and play it.
        
        Args:
            text (str): Text to speak
            blocking (bool): Whether to block until speech is complete
            
        Returns:
            bool: Success status
        """
        if not text:
            return False
        
        # Use pyttsx3 if available
        if self.engine:
            try:
                if blocking:
                    self.engine.say(text)
                    self.engine.runAndWait()
                else:
                    # Run in a separate thread
                    def speak_thread():
                        self.engine.say(text)
                        self.engine.runAndWait()
                    
                    thread = threading.Thread(target=speak_thread)
                    thread.daemon = True
                    thread.start()
                
                return True
            
            except Exception as e:
                logger.error(f"Error with pyttsx3: {e}")
                # Fall back to gTTS if pyttsx3 fails
                if self.gtts_available:
                    return self._speak_with_gtts(text, blocking)
                return False
        
        # Use gTTS if pyttsx3 not available
        elif self.gtts_available:
            return self._speak_with_gtts(text, blocking)
        
        # No TTS available
        else:
            logger.warning(f"No TTS engine available. Text: {text}")
            return False
    
    def _speak_with_gtts(self, text, blocking=False):
        """
        Use gTTS for text-to-speech.
        
        Args:
            text (str): Text to speak
            blocking (bool): Whether to block until speech is complete
            
        Returns:
            bool: Success status
        """
        try:
            from gtts import gTTS
            import os
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech
            tts = gTTS(text=text, lang='en')
            tts.save(temp_path)
            
            # Play the audio
            if blocking:
                self._play_audio(temp_path)
                os.unlink(temp_path)
            else:
                # Run in a separate thread
                def play_thread():
                    self._play_audio(temp_path)
                    os.unlink(temp_path)
                
                thread = threading.Thread(target=play_thread)
                thread.daemon = True
                thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error with gTTS: {e}")
            return False
    
    def _play_audio(self, file_path):
        """
        Play an audio file.
        
        Args:
            file_path (str): Path to audio file
        """
        try:
            # Try different audio players
            players = [
                ['mpg123', '-q'],  # Linux
                ['mpg321', '-q'],  # Linux alternative
                ['afplay'],        # macOS
                ['powershell', '-c', '(New-Object Media.SoundPlayer "{0}").PlaySync();']  # Windows
            ]
            
            import subprocess
            for player in players:
                cmd = player + [file_path] if player[-1] != '{0}' else player[:-1] + [player[-1].format(file_path)]
                try:
                    subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except:
                    continue
            
            logger.warning("Could not find a suitable audio player")
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def set_voice(self, voice):
        """
        Set the voice for TTS.
        
        Args:
            voice (str): Voice name
        """
        self.voice = voice
        
        if self.engine:
            voices = self.engine.getProperty('voices')
            for v in voices:
                if voice.lower() in v.name.lower():
                    self.engine.setProperty('voice', v.id)
                    logger.info(f"Set voice to {v.name}")
                    return True
            
            logger.warning(f"Voice '{voice}' not found")
        
        return False
    
    def set_rate(self, rate):
        """
        Set the speech rate.
        
        Args:
            rate (int): Speech rate (words per minute)
        """
        self.rate = rate
        
        if self.engine:
            self.engine.setProperty('rate', rate)
            logger.info(f"Set speech rate to {rate}")
            return True
        
        return False
    
    def set_volume(self, volume):
        """
        Set the volume level.
        
        Args:
            volume (float): Volume level (0.0-1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        
        if self.engine:
            self.engine.setProperty('volume', self.volume)
            logger.info(f"Set volume to {self.volume}")
            return True
        
        return False
    
    def get_available_voices(self):
        """
        Get list of available voices.
        
        Returns:
            list: Available voice names
        """
        if self.engine:
            voices = self.engine.getProperty('voices')
            return [v.name for v in voices]
        
        return []


class AudioOutputHandler:
    """Manages playback of responses and audio feedback."""
    
    def __init__(self, sound_effects_dir=None):
        """
        Initialize the audio output handler.
        
        Args:
            sound_effects_dir (str): Directory with sound effect files
        """
        self.sound_effects_dir = sound_effects_dir
        self.sound_effects = {
            "wake": "wake.mp3",
            "listening": "listening.mp3",
            "success": "success.mp3",
            "error": "error.mp3",
            "cancel": "cancel.mp3"
        }
    
    def play_sound(self, sound_name):
        """
        Play a sound effect.
        
        Args:
            sound_name (str): Name of sound effect to play
            
        Returns:
            bool: Success status
        """
        if not self.sound_effects_dir:
            return False
        
        sound_file = self.sound_effects.get(sound_name)
        if not sound_file:
            logger.warning(f"Sound effect '{sound_name}' not defined")
            return False
        
        sound_path = os.path.join(self.sound_effects_dir, sound_file)
        if not os.path.exists(sound_path):
            logger.warning(f"Sound file not found: {sound_path}")
            return False
        
        try:
            # Play in a separate thread
            def play_thread():
                self._play_audio(sound_path)
            
            thread = threading.Thread(target=play_thread)
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error playing sound: {e}")
            return False
    
    def _play_audio(self, file_path):
        """
        Play an audio file.
        
        Args:
            file_path (str): Path to audio file
        """
        try:
            # Try different audio players
            players = [
                ['mpg123', '-q'],  # Linux
                ['mpg321', '-q'],  # Linux alternative
                ['afplay'],        # macOS
                ['powershell', '-c', '(New-Object Media.SoundPlayer "{0}").PlaySync();']  # Windows
            ]
            
            import subprocess
            for player in players:
                cmd = player + [file_path] if player[-1] != '{0}' else player[:-1] + [player[-1].format(file_path)]
                try:
                    subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except:
                    continue
            
            logger.warning("Could not find a suitable audio player")
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def add_sound_effect(self, name, file_name):
        """
        Add a new sound effect.
        
        Args:
            name (str): Sound effect name
            file_name (str): Sound file name
        """
        self.sound_effects[name] = file_name
        logger.info(f"Added sound effect '{name}': {file_name}")


class ResponseGenerationModule:
    """Main response generation module that coordinates response formatting and delivery."""
    
    def __init__(self, templates_file=None, sound_effects_dir=None, voice=None, rate=200, volume=1.0):
        """
        Initialize the response generation module.
        
        Args:
            templates_file (str): Path to response templates file
            sound_effects_dir (str): Directory with sound effect files
            voice (str): TTS voice to use
            rate (int): Speech rate
            volume (float): Volume level
        """
        self.formatter = ResponseFormatter(templates_file)
        self.tts_engine = TextToSpeechEngine(voice, rate, volume)
        self.audio_handler = AudioOutputHandler(sound_effects_dir)
        
        # Callbacks
        self.on_response_start = None
        self.on_response_complete = None
    
    def generate_response(self, command_result, speak=True, sound=True):
        """
        Generate and deliver a response.
        
        Args:
            command_result (dict): Result from command processor
            speak (bool): Whether to speak the response
            sound (bool): Whether to play sound effects
            
        Returns:
            dict: Response data
        """
        # Format the text response
        text = self.formatter.format_response(command_result)
        
        # Create response data
        response = {
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "command_result": command_result
        }
        
        # Notify response start
        if self.on_response_start:
            self.on_response_start(response)
        
        # Play appropriate sound effect
        if sound:
            if command_result.get("success", False):
                self.audio_handler.play_sound("success")
            else:
                self.audio_handler.play_sound("error")
        
        # Speak the response if requested
        if speak:
            self.tts_engine.speak(text, blocking=False)
            
            # Give some time for TTS to start
            time.sleep(0.1)
        
        # Notify response complete
        if self.on_response_complete:
            self.on_response_complete(response)
        
        return response
    
    def play_wake_sound(self):
        """Play the wake sound effect."""
        return self.audio_handler.play_sound("wake")
    
    def play_listening_sound(self):
        """Play the listening sound effect."""
        return self.audio_handler.play_sound("listening")
    
    def speak_text(self, text, blocking=False):
        """
        Speak text without command processing.
        
        Args:
            text (str): Text to speak
            blocking (bool): Whether to block until speech is complete
            
        Returns:
            bool: Success status
        """
        return self.tts_engine.speak(text, blocking)
    
    def set_voice(self, voice):
        """
        Set the TTS voice.
        
        Args:
            voice (str): Voice name
        """
        return self.tts_engine.set_voice(voice)
    
    def set_rate(self, rate):
        """
        Set the speech rate.
        
        Args:
            rate (int): Speech rate
        """
        return self.tts_engine.set_rate(rate)
    
    def set_volume(self, volume):
        """
        Set the volume level.
        
        Args:
            volume (float): Volume level (0.0-1.0)
        """
        return self.tts_engine.set_volume(volume)
    
    def get_available_voices(self):
        """
        Get list of available voices.
        
        Returns:
            list: Available voice names
        """
        return self.tts_engine.get_available_voices()
    
    def add_response_template(self, intent, status, template):
        """
        Add a new response template.
        
        Args:
            intent (str): Intent name
            status (str): Status (success/failure)
            template (str): Response template
        """
        self.formatter.add_template(intent, status, template)
    
    def save_templates(self, templates_file):
        """
        Save templates to a file.
        
        Args:
            templates_file (str): Path to save templates
        """
        return self.formatter.save_templates(templates_file)


# Example usage
if __name__ == "__main__":
    # Create response generation module
    response_module = ResponseGenerationModule()
    
    # Test with some example command results
    test_results = [
        {
            "intent": "time",
            "success": True,
            "message": "",
            "data": {
                "time": "3:30 PM"
            }
        },
        {
            "intent": "set_timer",
            "success": True,
            "message": "",
            "data": {
                "minutes": 5,
                "seconds": 30
            }
        },
        {
            "intent": "unknown",
            "success": False,
            "message": "",
            "data": {}
        }
    ]
    
    for result in test_results:
        print(f"\nGenerating response for: {result['intent']}")
        response = response_module.generate_response(result, speak=False, sound=False)
        print(f"Response: {response['text']}")
    
    # Test TTS if available
    print("\nTesting text-to-speech...")
    response_module.speak_text("This is a test of the text to speech system.", blocking=True)
    
    print("\nAvailable voices:")
    voices = response_module.get_available_voices()
    for voice in voices:
        print(f"- {voice}")
