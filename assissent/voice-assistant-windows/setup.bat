@echo off
echo Voice Assistant Setup for Windows
echo ================================

echo Installing required dependencies...
pip install SpeechRecognition PyAudio numpy pyttsx3 vosk openai-whisper gtts nltk

echo Creating directories...
mkdir %USERPROFILE%\voice_assistant
mkdir %USERPROFILE%\voice_assistant\config
mkdir %USERPROFILE%\voice_assistant\models
mkdir %USERPROFILE%\voice_assistant\models\vosk
mkdir %USERPROFILE%\voice_assistant\sounds
mkdir %USERPROFILE%\voice_assistant\custom_skills

echo Copying files...
xcopy /E /I src %USERPROFILE%\voice_assistant\src
copy README.md %USERPROFILE%\voice_assistant\

echo Creating default configuration...
echo {
echo   "assistant_name": "Assistant",
echo   "wake_words": ["hey assistant", "okay computer"],
echo   "voice_recognition": {
echo     "vosk_model_path": null,
echo     "whisper_model_name": "base",
echo     "sample_rate": 16000,
echo     "chunk_size": 1024,
echo     "sensitivity": 0.5
echo   },
echo   "command_processing": {
echo     "custom_skills_dir": null
echo   },
echo   "response_generation": {
echo     "templates_file": null,
echo     "sound_effects_dir": null,
echo     "voice": null,
echo     "rate": 200,
echo     "volume": 1.0
echo   }
echo } > %USERPROFILE%\voice_assistant\config\config.json

echo Setup complete!
echo To start the voice assistant, run voice_assistant.bat
pause