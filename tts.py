import os
import sys
import torch
import numpy as np
import scipy.io.wavfile
from pydub import AudioSegment
import re
import time
import asyncio
import edge_tts
import config_audio as config

# Bark/XTTS imports (only if used as local engine)
if config.TTS_ENGINE in ["bark", "cloning"]:
    from transformers import AutoProcessor
    if config.TTS_ENGINE == "bark":
        from transformers import BarkModel
    else:
        # XTTS v2 for cloning - requires coqui-tts usually, but we'll use a robust pipeline
        # For simplicity, we'll implement XTTS if coqui-tts is installable, 
        # otherwise we'll advise the user on local setup.
        pass

if config.TTS_ENGINE == "elevenlabs":
    from elevenlabs.client import ElevenLabs
    from elevenlabs import save
    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)

os.makedirs(config.OUTPUT_DIR, exist_ok=True)

class HindiAudioGenerator:
    def __init__(self):
        self.engine = config.TTS_ENGINE
        print(f"🔄 Initializing Hindi TTS Engine: {self.engine}...")
        
        if self.engine == "bark":
            from transformers import BarkModel
            self.model = BarkModel.from_pretrained(config.MODEL_ID).to(config.DEVICE)
            self.model.eval()
            self.processor = AutoProcessor.from_pretrained(config.MODEL_ID)
            print("✅ Bark loaded.")
        elif self.engine == "cloning":
            print("🔬 Cloning mode active (Requires XTTS v2 setup).")
        elif self.engine == "elevenlabs":
            print(f"💎 ElevenLabs Cloud Mode (Voice: {config.ELEVENLABS_VOICE_ID})")
        else:
            print(f"✅ Edge-TTS ready (Voice: {config.VOICE_EDGE})")

    def split_text(self, text):
        # Determine chunk size based on engine
        if self.engine == "elevenlabs":
            max_len = 5000 # ElevenLabs can handle long text in one go
        elif self.engine == "edge-tts":
            max_len = config.MAX_CHUNK_LENGTH_EDGE
        else:
            max_len = config.MAX_CHUNK_LENGTH_BARK
            
        sentences = re.split(r'(?<=[.।!?])\s+', text)
        final_list = []
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(s) > max_len:
                parts = re.split(r'(?<=[,])\s+', s)
                for p in parts:
                    if len(p.strip()) > max_len:
                        words = p.split()
                        curr = ""
                        for w in words:
                            if len(curr) + len(w) < max_len:
                                curr += w + " "
                            else:
                                final_list.append(curr.strip())
                                curr = w + " "
                        if curr: final_list.append(curr.strip())
                    else:
                        final_list.append(p.strip())
            else:
                final_list.append(s)
        return final_list

    async def generate_edge_audio(self, text, output_path):
        import edge_tts
        communicate = edge_tts.Communicate(text, config.VOICE_EDGE)
        await communicate.save(output_path)

    def generate_elevenlabs_audio(self, text, output_path):
        print(f"   📡 Calling ElevenLabs API...")
        try:
            audio = client.generate(
                text=text,
                voice=config.ELEVENLABS_VOICE_ID,
                model="eleven_multilingual_v2"
            )
            save(audio, output_path)
            return True
        except Exception as e:
            print(f"❌ ElevenLabs Error: {e}")
            return False

    def generate_cloning_audio(self, text, output_path):
        import subprocess
        
        # Use absolute paths for sub-process safety
        ref_wav = os.path.abspath(config.CLONE_REFERENCE_WAV)
        output_path = os.path.abspath(output_path)
        
        # Check if we need to convert MP3 to WAV for XTTS
        if ref_wav.endswith(".mp3"):
            temp_ref = os.path.abspath("temp_ref_voice.wav")
            print(f"   🎵 Converting MP3 sample to WAV for better cloning...")
            try:
                AudioSegment.from_file(ref_wav).export(temp_ref, format="wav")
                ref_wav = temp_ref
            except Exception as e:
                print(f"⚠️ Warning: Conversion failed. {e}")

        python_310 = os.path.join(os.getcwd(), "cloning_env/bin/python3")
        cloner_script = "cloner.py"
        
        print(f"   🧬 Cloning your voice sample (This may involve a one-time 1.8GB model download)...")
        
        # Prepare environment with license agreement
        env = os.environ.copy()
        env["TTS_AGREEMENT"] = "1"
        env["COQUI_TOS_AGREED"] = "1"
        
        cmd = [python_310, cloner_script, text, ref_wav, output_path]
        
        try:
            # We use a larger timeout for the first run due to the download
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            if result.returncode == 0:
                print("      ✅ Sample replicated successfully.")
                return True
            else:
                print(f"❌ Cloning Failed!\nError details:\n{result.stdout}\n{result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Cloning Subprocess Error: {e}")
            return False

    def generate_long_audio(self, text, output_filename):
        chunks = self.split_text(text)
        print(f"📝 Total chunks to generate: {len(chunks)}")
        
        run_id = int(time.time())
        chunk_files = []
        
        for i, chunk in enumerate(chunks):
            print(f"   🎙️ Generating chunk {i+1}/{len(chunks)}...")
            temp_file = os.path.join(config.OUTPUT_DIR, f"run_{run_id}_chunk_{i}.wav")
            
            success = False
            if self.engine == "edge-tts":
                asyncio.run(self.generate_edge_audio(chunk, temp_file))
                success = True
            elif self.engine == "elevenlabs":
                success = self.generate_elevenlabs_audio(chunk, temp_file)
            elif self.engine == "cloning":
                success = self.generate_cloning_audio(chunk, temp_file)
            else:
                print("❌ Unsupported engine.")
                return
            
            if success and os.path.exists(temp_file):
                chunk_files.append(temp_file)
            
        if not chunk_files:
            print("❌ Error: No audio chunks generated.")
            return

        print(f"🔗 Merging into final professional recording...")
        combined = AudioSegment.empty()
        for f in chunk_files:
            try:
                segment = AudioSegment.from_file(f)
                combined += segment
                os.remove(f)
            except Exception as e:
                print(f"⚠️ Warning: {e}")
            
        combined.export(output_filename, format="wav")
        # Cleanup temp ref if created
        if os.path.exists("temp_ref_voice.wav"):
            os.remove("temp_ref_voice.wav")
            
        print(f"✅ Final replicated audio saved to: {output_filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python tts.py <text_file_path> [output_name] [voice_override]")
        return

    text_path = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "final_charming_audio.wav"
    if len(sys.argv) > 3:
        config.VOICE_EDGE = sys.argv[3]
        config.VOICE_BARK = sys.argv[3]
        print(f"🎙️ Speaker override: {sys.argv[3]}")

    try:
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ Error: {text_path} not found.")
        return

    generator = HindiAudioGenerator()
    generator.generate_long_audio(text, output_name)

if __name__ == "__main__":
    main()
