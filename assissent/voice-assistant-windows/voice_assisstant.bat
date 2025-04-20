@echo off
echo Installing required dependencies...
pip install SpeechRecognition PyAudio numpy pyttsx3 vosk openai-whisper gtts nltk

echo Starting Voice Assistant...
cd src
python main.py
pause