"""
Voice Recognition Module for Personal Voice Assistant

This module handles audio input, wake word detection, and speech-to-text conversion.
It implements a hybrid approach using multiple speech recognition engines.
"""

import os
import time
import threading
import queue
import logging
import numpy as np

# Will be imported conditionally to handle missing dependencies gracefully
# import speech_recognition as sr
# import pyaudio
# import whisper
# from vosk import Model, KaldiRecognizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('voice_recognition')

class AudioInputHandler:
    """Handles microphone input and audio processing."""
    
    def __init__(self, sample_rate=16000, chunk_size=1024):
        """
        Initialize the audio input handler.
        
        Args:
            sample_rate (int): Audio sample rate in Hz
            chunk_size (int): Size of audio chunks to process
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.thread = None
        self._setup_audio()
        
    def _setup_audio(self):
        """Set up the audio input system."""
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
            logger.info("PyAudio initialized successfully")
        except ImportError:
            logger.error("PyAudio not installed. Please install it with: pip install pyaudio")
            self.pyaudio = None
            
    def start_listening(self):
        """Start listening for audio input."""
        if not self.pyaudio:
            logger.error("Cannot start listening: PyAudio not initialized")
            return False
            
        if self.is_listening:
            logger.warning("Already listening")
            return True
            
        self.is_listening = True
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Started listening for audio input")
        return True
        
    def stop_listening(self):
        """Stop listening for audio input."""
        self.is_listening = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        logger.info("Stopped listening for audio input")
        
    def _listen_loop(self):
        """Continuously capture audio and add to queue."""
        try:
            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(2),  # 16-bit
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while self.is_listening:
                try:
                    audio_data = stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_queue.put(audio_data)
                except Exception as e:
                    logger.error(f"Error reading audio: {e}")
                    time.sleep(0.1)
                    
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
            self.is_listening = False
            
    def get_audio_chunk(self, block=True, timeout=None):
        """
        Get a chunk of audio from the queue.
        
        Args:
            block (bool): Whether to block until data is available
            timeout (float): Maximum time to block in seconds
            
        Returns:
            bytes: Audio data or None if timeout
        """
        try:
            return self.audio_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
            
    def __del__(self):
        """Clean up resources."""
        self.stop_listening()
        if self.pyaudio:
            self.pyaudio.terminate()


class WakeWordDetector:
    """Detects wake words using Vosk for efficient, low-latency detection."""
    
    def __init__(self, wake_words=None, model_path=None, sensitivity=0.5):
        """
        Initialize the wake word detector.
        
        Args:
            wake_words (list): List of wake word phrases
            model_path (str): Path to Vosk model directory
            sensitivity (float): Detection sensitivity (0.0-1.0)
        """
        self.wake_words = wake_words or ["hey assistant"]
        self.model_path = model_path
        self.sensitivity = sensitivity
        self.recognizer = None
        self._setup_vosk()
        
    def _setup_vosk(self):
        """Set up the Vosk recognizer."""
        try:
            from vosk import Model, KaldiRecognizer
            
            # Use default model path if not specified
            if not self.model_path:
                self.model_path = os.path.join(os.path.expanduser("~"), "voice_assistant", "models", "vosk-model-small-en-us-0.15")
                
            # Check if model exists
            if not os.path.exists(self.model_path):
                logger.warning(f"Vosk model not found at {self.model_path}. Wake word detection will not work.")
                logger.info("Please download a model from https://alphacephei.com/vosk/models")
                return
                
            # Initialize model and recognizer
            model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(model, 16000)
            logger.info("Vosk wake word detector initialized successfully")
            
        except ImportError:
            logger.error("Vosk not installed. Please install it with: pip install vosk")
            self.recognizer = None
            
    def process_audio(self, audio_data):
        """
        Process audio data to detect wake words.
        
        Args:
            audio_data (bytes): Raw audio data
            
        Returns:
            bool: True if wake word detected, False otherwise
        """
        if not self.recognizer:
            return False
            
        try:
            if self.recognizer.AcceptWaveform(audio_data):
                result = self.recognizer.Result()
                import json
                text = json.loads(result).get("text", "").lower()
                
                # Check if any wake word is in the recognized text
                for wake_word in self.wake_words:
                    if wake_word.lower() in text:
                        logger.info(f"Wake word detected: {wake_word}")
                        return True
                        
        except Exception as e:
            logger.error(f"Error processing audio for wake word: {e}")
            
        return False


class SpeechRecognizer:
    """Converts speech to text using a hybrid approach with multiple engines."""
    
    def __init__(self, vosk_model_path=None, whisper_model_name="base"):
        """
        Initialize the speech recognizer.
        
        Args:
            vosk_model_path (str): Path to Vosk model directory
            whisper_model_name (str): Name of Whisper model to use
        """
        self.vosk_model_path = vosk_model_path
        self.whisper_model_name = whisper_model_name
        self.sr_recognizer = None
        self.vosk_recognizer = None
        self.whisper_model = None
        self._setup_recognizers()
        
    def _setup_recognizers(self):
        """Set up all speech recognition engines."""
        # Setup SpeechRecognition
        try:
            import speech_recognition as sr
            self.sr_recognizer = sr.Recognizer()
            logger.info("SpeechRecognition initialized successfully")
        except ImportError:
            logger.error("SpeechRecognition not installed. Please install it with: pip install SpeechRecognition")
            self.sr_recognizer = None
            
        # Setup Vosk
        try:
            from vosk import Model, KaldiRecognizer
            
            # Use default model path if not specified
            if not self.vosk_model_path:
                self.vosk_model_path = os.path.join(os.path.expanduser("~"), "voice_assistant", "models", "vosk-model-small-en-us-0.15")
                
            # Check if model exists
            if os.path.exists(self.vosk_model_path):
                model = Model(self.vosk_model_path)
                self.vosk_recognizer = KaldiRecognizer(model, 16000)
                logger.info("Vosk recognizer initialized successfully")
            else:
                logger.warning(f"Vosk model not found at {self.vosk_model_path}")
                
        except ImportError:
            logger.error("Vosk not installed. Please install it with: pip install vosk")
            self.vosk_recognizer = None
            
        # Setup Whisper
        try:
            import whisper
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            logger.info(f"Whisper model '{self.whisper_model_name}' loaded successfully")
        except ImportError:
            logger.error("Whisper not installed. Please install it with: pip install openai-whisper")
            self.whisper_model = None
            
    def recognize_with_vosk(self, audio_data):
        """
        Recognize speech using Vosk.
        
        Args:
            audio_data (bytes): Raw audio data
            
        Returns:
            str: Recognized text or empty string if failed
        """
        if not self.vosk_recognizer:
            return ""
            
        try:
            if self.vosk_recognizer.AcceptWaveform(audio_data):
                result = self.vosk_recognizer.Result()
                import json
                return json.loads(result).get("text", "")
        except Exception as e:
            logger.error(f"Error recognizing with Vosk: {e}")
            
        return ""
        
    def recognize_with_whisper(self, audio_data, sample_rate=16000):
        """
        Recognize speech using Whisper.
        
        Args:
            audio_data (bytes): Raw audio data
            sample_rate (int): Audio sample rate in Hz
            
        Returns:
            str: Recognized text or empty string if failed
        """
        if not self.whisper_model:
            return ""
            
        try:
            # Convert bytes to numpy array
            import numpy as np
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Recognize with Whisper
            result = self.whisper_model.transcribe(audio_np, fp16=False)
            return result.get("text", "")
            
        except Exception as e:
            logger.error(f"Error recognizing with Whisper: {e}")
            
        return ""
        
    def recognize_with_sr(self, audio_data, sample_rate=16000):
        """
        Recognize speech using SpeechRecognition.
        
        Args:
            audio_data (bytes): Raw audio data
            sample_rate (int): Audio sample rate in Hz
            
        Returns:
            str: Recognized text or empty string if failed
        """
        if not self.sr_recognizer:
            return ""
            
        try:
            import speech_recognition as sr
            
            # Convert bytes to AudioData
            audio = sr.AudioData(audio_data, sample_rate, 2)
            
            # Try to recognize with Sphinx (offline)
            try:
                return self.sr_recognizer.recognize_sphinx(audio)
            except (sr.UnknownValueError, sr.RequestError) as e:
                logger.debug(f"Sphinx recognition failed: {e}")
                
            # Fallback to Google (online)
            try:
                return self.sr_recognizer.recognize_google(audio)
            except (sr.UnknownValueError, sr.RequestError) as e:
                logger.debug(f"Google recognition failed: {e}")
                
        except Exception as e:
            logger.error(f"Error recognizing with SpeechRecognition: {e}")
            
        return ""
        
    def recognize(self, audio_data, engine="auto", sample_rate=16000):
        """
        Recognize speech using the best available engine.
        
        Args:
            audio_data (bytes): Raw audio data
            engine (str): Preferred engine ('vosk', 'whisper', 'sr', or 'auto')
            sample_rate (int): Audio sample rate in Hz
            
        Returns:
            dict: Recognition result with text and metadata
        """
        result = {
            "text": "",
            "engine": None,
            "confidence": 0.0,
            "success": False
        }
        
        # Try the specified engine first
        if engine == "vosk" and self.vosk_recognizer:
            result["text"] = self.recognize_with_vosk(audio_data)
            result["engine"] = "vosk"
            result["success"] = bool(result["text"])
            
        elif engine == "whisper" and self.whisper_model:
            result["text"] = self.recognize_with_whisper(audio_data, sample_rate)
            result["engine"] = "whisper"
            result["success"] = bool(result["text"])
            
        elif engine == "sr" and self.sr_recognizer:
            result["text"] = self.recognize_with_sr(audio_data, sample_rate)
            result["engine"] = "sr"
            result["success"] = bool(result["text"])
            
        # Auto mode - try engines in order of preference
        elif engine == "auto":
            # For short commands, try Vosk first (faster)
            if self.vosk_recognizer:
                result["text"] = self.recognize_with_vosk(audio_data)
                result["engine"] = "vosk"
                
            # If Vosk failed or returned short result, try Whisper (more accurate)
            if (not result["text"] or len(result["text"].split()) < 3) and self.whisper_model:
                whisper_text = self.recognize_with_whisper(audio_data, sample_rate)
                if whisper_text:
                    result["text"] = whisper_text
                    result["engine"] = "whisper"
                    
            # Last resort, try SpeechRecognition
            if not result["text"] and self.sr_recognizer:
                sr_text = self.recognize_with_sr(audio_data, sample_rate)
                if sr_text:
                    result["text"] = sr_text
                    result["engine"] = "sr"
                    
            result["success"] = bool(result["text"])
            
        else:
            logger.error(f"Unknown engine: {engine}")
            
        return result


class VoiceRecognitionModule:
    """Main voice recognition module that coordinates audio input, wake word detection, and speech recognition."""
    
    def __init__(self, 
                 wake_words=None,
                 vosk_model_path=None, 
                 whisper_model_name="base",
                 sample_rate=16000,
                 chunk_size=1024,
                 sensitivity=0.5):
        """
        Initialize the voice recognition module.
        
        Args:
            wake_words (list): List of wake word phrases
            vosk_model_path (str): Path to Vosk model directory
            whisper_model_name (str): Name of Whisper model to use
            sample_rate (int): Audio sample rate in Hz
            chunk_size (int): Size of audio chunks to process
            sensitivity (float): Wake word detection sensitivity
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        # Initialize components
        self.audio_handler = AudioInputHandler(sample_rate, chunk_size)
        self.wake_detector = WakeWordDetector(wake_words, vosk_model_path, sensitivity)
        self.speech_recognizer = SpeechRecognizer(vosk_model_path, whisper_model_name)
        
        # State variables
        self.is_running = False
        self.is_listening_for_command = False
        self.command_timeout = 10.0  # seconds
        self.command_buffer = bytearray()
        
        # Callback functions
        self.on_wake_word = None
        self.on_command = None
        self.on_timeout = None
        self.on_error = None
        
    def start(self):
        """Start the voice recognition module."""
        if self.is_running:
            logger.warning("Voice recognition module is already running")
            return False
            
        # Start audio input
        if not self.audio_handler.start_listening():
            if self.on_error:
                self.on_error("Failed to start audio input")
            return False
            
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info("Voice recognition module started")
        return True
        
    def stop(self):
        """Stop the voice recognition module."""
        self.is_running = False
        self.is_listening_for_command = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
            self.processing_thread = None
            
        self.audio_handler.stop_listening()
        logger.info("Voice recognition module stopped")
        
    def _processing_loop(self):
        """Main processing loop for voice recognition."""
        try:
            while self.is_running:
                # Get audio chunk
                audio_chunk = self.audio_handler.get_audio_chunk(timeout=0.1)
                if not audio_chunk:
                    continue
                    
                # If we're listening for a command, add to buffer
                if self.is_listening_for_command:
                    self._process_command_audio(audio_chunk)
                    continue
                    
                # Otherwise, check for wake word
                if self.wake_detector.process_audio(audio_chunk):
                    self._wake_word_detected()
                    
        except Exception as e:
            logger.error(f"Error in processing loop: {e}")
            if self.on_error:
                self.on_error(f"Processing error: {e}")
            self.is_running = False
            
    def _wake_word_detected(self):
        """Handle wake word detection."""
        logger.info("Wake word detected, listening for command")
        
        # Notify callback
        if self.on_wake_word:
            self.on_wake_word()
            
        # Start listening for command
        self.is_listening_for_command = True
        self.command_buffer = bytearray()
        self.command_start_time = time.time()
        
    def _process_command_audio(self, audio_chunk):
        """Process audio for command recognition."""
        # Add to buffer
        self.command_buffer.extend(audio_chunk)
        
        # Check for timeout
        elapsed = time.time() - self.command_start_time
        if elapsed > self.command_timeout:
            logger.info("Command timeout")
            if self.on_timeout:
                self.on_timeout()
            self.is_listening_for_command = False
            self.command_buffer = bytearray()
            return
            
        # Check if we have enough audio to process
        # Process command after ~2 seconds of silence or 5 seconds total
        buffer_duration = len(self.command_buffer) / (2 * self.sample_rate)  # 16-bit audio = 2 bytes per sample
        
        if buffer_duration >= 5.0 or (buffer_duration >= 2.0 and self._detect_silence(audio_chunk)):
            self._recognize_command()
            
    def _detect_silence(self, audio_chunk, threshold=500):
        """
        Detect if an audio chunk is silence.
        
        Args:
            audio_chunk (bytes): Audio data
            threshold (int): Silence threshold
            
        Returns:
            bool: True if silence detected
        """
        try:
            import numpy as np
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16)
            return np.max(np.abs(audio_np)) < threshold
        except:
            return False
            
    def _recognize_command(self):
        """Recognize the command from the buffer."""
        logger.info("Recognizing command")
        
        # Use Whisper for command recognition (more accurate)
        result = self.speech_recognizer.recognize(bytes(self.command_buffer), engine="whisper", sample_rate=self.sample_rate)
        
        # Reset state
        self.is_listening_for_command = False
        self.command_buffer = bytearray()
        
        # Notify callback
        if result["success"] and self.on_command:
            self.on_command(result)
        elif not result["success"] and self.on_error:
            self.on_error("Failed to recognize command")
            
    def set_wake_words(self, wake_words):
        """
        Set new wake words.
        
        Args:
            wake_words (list): List of wake word phrases
        """
        self.wake_detector.wake_words = wake_words
        logger.info(f"Wake words updated: {wake_words}")
        
    def set_sensitivity(self, sensitivity):
        """
        Set wake word detection sensitivity.
        
        Args:
            sensitivity (float): Detection sensitivity (0.0-1.0)
        """
        self.wake_detector.sensitivity = max(0.0, min(1.0, sensitivity))
        logger.info(f"Sensitivity updated: {self.wake_detector.sensitivity}")


# Example usage
if __name__ == "__main__":
    def on_wake_word():
        print("Wake word detected! Listening for command...")
        
    def on_command(result):
        print(f"Command recognized ({result['engine']}): {result['text']}")
        
    def on_timeout():
        print("Command timeout. Please try again.")
        
    def on_error(error):
        print(f"Error: {error}")
        
    # Create and configure the voice recognition module
    voice_module = VoiceRecognitionModule(
        wake_words=["hey assistant", "okay computer"],
        whisper_model_name="base",  # Use smaller model for faster processing
    )
    
    # Set callbacks
    voice_module.on_wake_word = on_wake_word
    voice_module.on_command = on_command
    voice_module.on_timeout = on_timeout
    voice_module.on_error = on_error
    
    # Start the module
    print("Starting voice recognition module...")
    print("Say 'hey assistant' or 'okay computer' to activate")
    voice_module.start()
    
    try:
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        voice_module.stop()
        print("Voice recognition module stopped")
