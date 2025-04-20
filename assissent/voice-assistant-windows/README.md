# Personal Voice Assistant User Guide

## Introduction

Welcome to your Personal Voice Assistant! This guide will help you set up, configure, and use your fully customizable voice assistant. This assistant is designed to give you complete control over all aspects of its functionality, from voice recognition to command processing to response generation.

## Features

- **Fully Offline Operation**: Your privacy is protected with local processing of voice commands
- **Customizable Wake Words**: Choose the phrases that activate your assistant
- **Multiple Recognition Engines**: Uses a hybrid approach with Vosk, Whisper, and SpeechRecognition
- **Extensible Skills System**: Add new capabilities through the plugin architecture
- **Configurable Responses**: Customize how your assistant responds to commands
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

## System Requirements

- Python 3.9 or higher
- Microphone for voice input
- Speakers for voice output
- Minimum 4GB RAM (8GB recommended for better performance)
- 1GB free disk space (more if using larger speech models)

## Installation

### Quick Installation

1. Clone or download the voice assistant repository
2. Navigate to the project directory
3. Run the setup script:

```bash
python src/setup.py
```

This will:
- Create the necessary directory structure
- Install required dependencies
- Generate a default configuration file

For offline speech recognition, add the `--download-vosk` flag:

```bash
python src/setup.py --download-vosk
```

### Manual Installation

If you prefer to install components manually:

1. Install the required Python packages:

```bash
pip install SpeechRecognition PyAudio numpy pyttsx3
```

2. For offline speech recognition, install additional packages:

```bash
pip install vosk openai-whisper
```

3. For text-to-speech functionality:

```bash
pip install pyttsx3 gtts
```

4. Create a configuration file (see Configuration section)

## Starting the Voice Assistant

After installation, start the voice assistant with:

```bash
python src/main.py
```

If you created a custom configuration file:

```bash
python src/main.py --config /path/to/your/config.json
```

## Using the Voice Assistant

1. **Activate the assistant** by saying one of the wake words (default: "hey assistant" or "okay computer")
2. **Wait for the acknowledgment sound** indicating the assistant is listening
3. **Speak your command** clearly
4. **Listen for the response** from the assistant

### Example Commands

- "What time is it?"
- "What's the date today?"
- "Set a timer for 5 minutes"
- "How much time is left on my timer?"
- "Help me" or "What can you do?"

## Configuration

The voice assistant can be configured through a JSON configuration file. The default location is `~/voice_assistant/config/config.json`.

### Configuration Options

```json
{
  "assistant_name": "Assistant",
  "wake_words": ["hey assistant", "okay computer"],
  "voice_recognition": {
    "vosk_model_path": null,
    "whisper_model_name": "base",
    "sample_rate": 16000,
    "chunk_size": 1024,
    "sensitivity": 0.5
  },
  "command_processing": {
    "custom_skills_dir": null
  },
  "response_generation": {
    "templates_file": null,
    "sound_effects_dir": null,
    "voice": null,
    "rate": 200,
    "volume": 1.0
  }
}
```

### Key Configuration Parameters

- **assistant_name**: Name of your assistant
- **wake_words**: List of phrases that activate the assistant
- **voice_recognition.whisper_model_name**: Size of the Whisper model ("tiny", "base", "small", "medium", "large")
- **voice_recognition.sensitivity**: Wake word detection sensitivity (0.0-1.0)
- **response_generation.voice**: TTS voice to use (null for system default)
- **response_generation.rate**: Speech rate (words per minute)
- **response_generation.volume**: Volume level (0.0-1.0)

## Extending the Assistant

### Adding Custom Skills

You can extend the assistant's capabilities by creating custom skills:

1. Create a new Python file in your custom skills directory
2. Define a class that inherits from the `Skill` base class
3. Implement the `register_intents` and `handle` methods
4. Update your configuration to point to your custom skills directory

Example custom skill:

```python
from src.command_processing import Skill

class WeatherSkill(Skill):
    def register_intents(self):
        self.intents = ["weather"]
        self.command_processor.intent_parser.add_intent_pattern(
            "weather", r"what('s| is) the weather( like)?( in (.+))?"
        )
    
    def handle(self, intent_data):
        # Extract location if provided
        location = "your location"
        if "entity_1" in intent_data["entities"]:
            location = intent_data["entities"]["entity_1"]
        
        # In a real implementation, you would call a weather API here
        return {
            "success": True,
            "message": f"The weather in {location} is sunny and 72 degrees.",
            "data": {
                "location": location,
                "condition": "sunny",
                "temperature": 72
            }
        }
```

### Customizing Responses

You can customize how the assistant responds to commands by creating a response templates file:

1. Create a JSON file with your custom templates
2. Update your configuration to point to this file

Example templates file:

```json
{
  "time": {
    "success": "It's currently {time}."
  },
  "weather": {
    "success": "In {location}, it's {condition} with a temperature of {temperature} degrees."
  }
}
```

## Troubleshooting

### Common Issues

**Problem**: Assistant doesn't respond to wake word
**Solution**: 
- Check your microphone is working
- Increase the sensitivity in the configuration
- Try speaking louder or closer to the microphone

**Problem**: "PyAudio not installed" error
**Solution**:
- On Windows: `pip install pipwin` then `pipwin install pyaudio`
- On macOS: `brew install portaudio` then `pip install pyaudio`
- On Linux: `sudo apt-get install python3-dev portaudio19-dev` then `pip install pyaudio`

**Problem**: High CPU usage
**Solution**: Use a smaller Whisper model by setting `whisper_model_name` to "tiny" or "base"

## Project Structure

```
voice_assistant/
├── src/                      # Source code
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Main application
│   ├── setup.py              # Setup script
│   ├── voice_recognition.py  # Voice recognition module
│   ├── command_processing.py # Command processing module
│   ├── response_generation.py # Response generation module
│   └── test_voice_assistant.py # Test script
├── models/                   # Speech recognition models
│   └── vosk/                 # Vosk models
├── config/                   # Configuration files
│   └── config.json           # Main configuration
├── sounds/                   # Sound effects
└── custom_skills/            # Custom skill plugins
```

## Advanced Usage

### Running Tests

To run the test suite:

```bash
python src/test_voice_assistant.py
```

### Debugging

Enable debug logging by setting the logging level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tuning

For better performance on lower-end systems:
- Use the "tiny" Whisper model
- Reduce the sample rate to 8000
- Increase the chunk size to 2048

## Privacy Considerations

This voice assistant is designed with privacy in mind:
- All speech processing happens locally on your device
- No data is sent to external servers (unless you use online services)
- All configuration and history is stored locally

## License

This voice assistant is provided under the MIT License. You are free to modify, distribute, and use it for any purpose.

## Support

For issues, questions, or contributions, please contact the developer or submit an issue on the project repository.

---

Enjoy your fully controlled personal voice assistant!
