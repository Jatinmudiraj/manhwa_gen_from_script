import os
import sys
import subprocess
import time
import math
import glob
from pydub.utils import mediainfo

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_GEN_DIR = os.path.dirname(BASE_DIR)
AUDIO_GEN_DIR = BASE_DIR

AUDIO_ENV_PYTHON = os.path.join(AUDIO_GEN_DIR, "audio_env/bin/python3")
IMG_ENV_PYTHON = os.path.join(IMG_GEN_DIR, "img_env/bin/python3")

HINDI_TEXT_FILE = os.path.join(AUDIO_GEN_DIR, "hindi_text.txt")
PROMPTS_FILE = os.path.join(IMG_GEN_DIR, "prompts.txt")

OUTPUT_VIDEO_DIR = os.path.join(AUDIO_GEN_DIR, "video_generated")
CLIPS_DIR = os.path.join(AUDIO_GEN_DIR, "clips")
IMG_OUTPUT_DIR = os.path.join(IMG_GEN_DIR, "output")

def get_audio_duration(audio_path):
    info = mediainfo(audio_path)
    return float(info['duration'])

def run_command(cmd, cwd=None):
    print(f"🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    return True

def main():
    print("🎬 Starting Automatic Video Generator...")
    
    # 1. Generate Audio
    audio_output = os.path.join(AUDIO_GEN_DIR, "temp_story_audio.wav")
    print("\n   🎙️ Step 1: Generating Cloned Audio...")
    # Using environment variable for agreement
    env = os.environ.copy()
    env["TTS_AGREEMENT"] = "1"
    
    cmd_audio = [AUDIO_ENV_PYTHON, "tts.py", "hindi_text.txt", "temp_story_audio.wav"]
    if not run_command(cmd_audio, cwd=AUDIO_GEN_DIR):
        print("❌ Audio generation failed.")
        return

    duration = get_audio_duration(audio_output)
    print(f"   ✅ Audio generated. Duration: {duration:.2f} seconds")

    # 2. Determine number of images needed (8 seconds per image)
    num_images_needed = math.ceil(duration / 8.0)
    print(f"   🖼️ Step 2: Need {num_images_needed} images for synchronization.")

    # 3. Generate Images
    print("\n   🎨 Step 3: Generating Story Images...")
    # Note: gen.py generates IMAGES_PER_PROMPT (2) per prompt line.
    # We'll just run it as is and pick one per prompt.
    cmd_img = [IMG_ENV_PYTHON, "gen.py"]
    if not run_command(cmd_img, cwd=IMG_GEN_DIR):
        print("❌ Image generation failed.")
        return

    # 4. Filter and prepare image list
    # gen.py saves images as {prompt_idx+1:03d}_{char_prefix}_{seed}.png
    all_images = sorted(glob.glob(os.path.join(IMG_OUTPUT_DIR, "*.png")))
    
    # We want one image per prompt index. 
    # Since gen.py generates 2 per prompt, they come in pairs.
    unique_images = []
    seen_indices = set()
    for img in all_images:
        basename = os.path.basename(img)
        match = re.match(r"(\d+)_", basename)
        if match:
            idx = match.group(1)
            if idx not in seen_indices:
                unique_images.append(img)
                seen_indices.add(idx)
        
        if len(unique_images) >= num_images_needed:
            break

    if len(unique_images) < num_images_needed:
        print(f"⚠️ Warning: Only found {len(unique_images)} images, but need {num_images_needed}. Will loop them.")
        while len(unique_images) < num_images_needed:
            unique_images.append(unique_images[len(unique_images) % len(unique_images)])

    # 5. Create Video Clips (8 seconds per image)
    print("\n   ✂️ Step 4: Creating Video Clips...")
    clip_files = []
    for i, img_path in enumerate(unique_images[:num_images_needed]):
        clip_path = os.path.join(CLIPS_DIR, f"clip_{i:03d}.mp4")
        # Ensure it lasts exactly 8 seconds
        cmd_clip = [
            "ffmpeg", "-y", "-loop", "1", "-t", "8", "-i", img_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720",
            clip_path
        ]
        if run_command(cmd_clip):
            clip_files.append(clip_path)

    # 6. Merge Clips and Audio
    print("\n   🎬 Step 5: Final Assembly...")
    list_file = os.path.join(AUDIO_GEN_DIR, "clips_list.txt")
    with open(list_file, "w") as f:
        for clip in clip_files:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    final_video_no_audio = os.path.join(AUDIO_GEN_DIR, "temp_video_no_audio.mp4")
    # Concat clips
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", final_video_no_audio
    ])

    final_video = os.path.join(OUTPUT_VIDEO_DIR, "final_story_video.mp4")
    # Add audio and trim video to audio duration
    subprocess.run([
        "ffmpeg", "-y", "-i", final_video_no_audio, "-i", audio_output,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-t", str(duration), final_video
    ])

    # Cleanup
    print("\n   🧹 Step 6: Cleaning up temporary files...")
    os.remove(audio_output)
    os.remove(final_video_no_audio)
    os.remove(list_file)
    for f in clip_files:
        os.remove(f)

    print(f"\n✅ SUCCESS! Video saved to: {final_video}")

if __name__ == "__main__":
    import re
    main()
