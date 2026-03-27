# Hindi Audio Generation Configuration

# Engine to use: 
# "cloning" (Locally clones voices like Manav/Neel for free, needs a sample)
# "elevenlabs" (Premium, high quality Neal voice, costs money)
# "edge-tts" (Studio quality Microsoft voices, no echo, free)
# "bark" (Generative, emotional, free)
TTS_ENGINE = "cloning"

# Voice Cloning (XTTS v2) Settings
# Provide a clean sample from the audio_sample directory
CLONE_REFERENCE_WAV = "audio_sample/voice_preview_kanika – romantic, intimate & relatable.mp3" 

# ElevenLabs Settings
ELEVENLABS_API_KEY = "YOUR_API_KEY_HERE"
ELEVENLABS_VOICE_ID = "thT5L15f5v4Onz15z15z" 

# Edge-TTS Hindi Voice Options:
# "hi-IN-MadhurNeural" (Male, Charming, Professional)
# "hi-IN-SwaraNeural" (Female, Clear, Expressive)
VOICE_EDGE = "hi-IN-MadhurNeural"

# Output Directory
OUTPUT_DIR = "generated_audio"

# Stable CPU mode for local engines
DEVICE = "cpu"

# Text Processing limits
MAX_CHUNK_LENGTH_BARK = 150
MAX_CHUNK_LENGTH_EDGE = 1500
