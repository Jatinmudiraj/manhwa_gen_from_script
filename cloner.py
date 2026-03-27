import sys
import os
import torch
import functools

# Force CPU to avoid CUDA sm_60 incompatibility issues
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# --- MONKEYPATCH TORCH.LOAD FOR PYTORCH 2.6+ ---
# XTTS v2 uses custom classes in its weights that are blocked by weights_only=True
original_load = torch.load

@functools.wraps(original_load)
def patched_load(*args, **kwargs):
    # Force weights_only=False for the model weights
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_load(*args, **kwargs)

torch.load = patched_load
# ---------------------------------------------

try:
    from TTS.api import TTS
except ImportError:
    print("❌ TTS core not installed properly.")
    sys.exit(1)

def main():
    if len(sys.argv) < 4:
        print("Usage: python cloner.py <text> <ref_wav> <output_wav>")
        return

    text = sys.argv[1]
    ref_wav = sys.argv[2]
    output_wav = sys.argv[3]

    print(f"🔬 XTTS v2: Replicating voice from {ref_wav} (CPU Mode)...")
    
    device = "cpu"
    
    try:
        # Load model
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        
        # Generate with specific stability parameters
        # temperature=0.7, top_p=0.8 are often good for reducing "hallucinations"
        tts.tts_to_file(
            text=text,
            speaker_wav=ref_wav,
            language="hi",
            file_path=output_wav,
            temperature=0.7,
            top_p=0.8,
            speed=1.0,
            enable_text_splitting=False # Handled by our main tts.py
        )
        print(f"✅ Voice replication complete: {output_wav}")
    except Exception as e:
        print(f"❌ XTTS Engine Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
