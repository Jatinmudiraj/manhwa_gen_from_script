import os
import sys
import subprocess
import json
import math
import glob
from pydub.utils import mediainfo

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_GEN_DIR = os.path.dirname(BASE_DIR)
AUDIO_GEN_DIR = BASE_DIR

AUDIO_ENV_PYTHON = os.path.join(AUDIO_GEN_DIR, "audio_env/bin/python3")
IMG_ENV_PYTHON = os.path.join(IMG_GEN_DIR, "img_env/bin/python3")

CONFIG_FILE = os.path.join(AUDIO_GEN_DIR, "story_config.json")
OUTPUT_VIDEO_DIR = os.path.join(AUDIO_GEN_DIR, "video_generated")
CLIPS_DIR = os.path.join(AUDIO_GEN_DIR, "clips")
TEMP_DIR = os.path.join(AUDIO_GEN_DIR, "temp_assembly")

os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def get_audio_duration(audio_path):
    try:
        info = mediainfo(audio_path)
        return float(info['duration'])
    except:
        return 0.0

def run_command(cmd, cwd=None, env=None):
    print(f"🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    return True

def main():
    print("🎬 Starting V2 Video Generator (Scene-Synced)...")
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Error: {CONFIG_FILE} not found!")
        return

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        scenes = json.load(f)

    print(f"📝 Loaded {len(scenes)} scenes from config.")

    # 1. Pre-generate Images
    print("\n   🎨 Step 1: Pre-generating all story images...")
    img_files = glob.glob(os.path.join(IMG_GEN_DIR, "output", "*.png"))
    if len(img_files) < len(scenes) * 1.5:  # Rough check if we have ~2 images per prompt
        cmd_img = [IMG_ENV_PYTHON, "gen.py"]
        run_command(cmd_img, cwd=IMG_GEN_DIR)
    else:
        print("   ✅ Images already exist, skipping generation phase.")

    scene_video_files = []
    
    env = os.environ.copy()
    env["TTS_AGREEMENT"] = "1"

    for i, scene in enumerate(scenes):
        scene_id = scene.get('scene_id', i+1)
        text = scene['text']
        scene_prompts = scene['prompts']
        
        print(f"\n🎬 Processing Scene {scene_id}/{len(scenes)}...")
        
        # A. Generate Scene Audio
        scene_audio = os.path.join(TEMP_DIR, f"scene_{scene_id}.wav")
        # We need a temp text file for tts.py
        temp_text_file = os.path.join(TEMP_DIR, f"scene_{scene_id}.txt")
        with open(temp_text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        cmd_audio = [AUDIO_ENV_PYTHON, "tts.py", temp_text_file, scene_audio]
        if not run_command(cmd_audio, cwd=AUDIO_GEN_DIR, env=env):
            print(f"⚠️ Warning: Audio failed for scene {scene_id}, skipping.")
            continue
            
        scene_duration = get_audio_duration(scene_audio)
        if scene_duration <= 0:
            print(f"⚠️ Warning: Audio duration is 0 for scene {scene_id}, skipping.")
            continue
            
        print(f"   🎙️ Audio Duration: {scene_duration:.2f}s")

        # B. Get Images for this scene
        img_pattern = os.path.join(IMG_GEN_DIR, "output", f"{scene_id:03d}_*.png")
        found_images = sorted(glob.glob(img_pattern))
        
        if not found_images:
            print(f"⚠️ No images found for scene {scene_id}. Looking for fallback...")
            found_images = sorted(glob.glob(os.path.join(IMG_GEN_DIR, "output", "*.png")))[:1]

        # C. Calculate per-image duration
        img_duration = scene_duration / len(found_images)
        print(f"   🖼️ Distributing {len(found_images)} images over {scene_duration:.2f}s ({img_duration:.2f}s each)")

        # D. Create clips for this scene with Zoom effect
        scene_clips = []
        fps = 25
        for j, img_path in enumerate(found_images):
            clip_path = os.path.join(CLIPS_DIR, f"scene_{scene_id}_clip_{j}.mp4")
            
            # Zoom formula: Increase by 20% over duration
            zoom_inc = 0.2 / (fps * img_duration)
            zoom_filter = (
                f"zoompan=z='min(zoom+{zoom_inc},1.2)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={int(fps * img_duration)}:s=1440x810,scale=1280:720"
            )
            
            cmd_clip = [
                "ffmpeg", "-y", "-i", img_path,
                "-vf", zoom_filter,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                "-t", str(img_duration),
                clip_path
            ]
            if run_command(cmd_clip):
                scene_clips.append(clip_path)

        # E. Merge clips into scene video with audio
        scene_video_no_audio = os.path.join(TEMP_DIR, f"scene_{scene_id}_no_audio.mp4")
        list_file = os.path.join(TEMP_DIR, f"scene_{scene_id}_list.txt")
        with open(list_file, "w") as f:
            for c in scene_clips:
                f.write(f"file '{os.path.abspath(c)}'\n")
        
        run_command(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", scene_video_no_audio])
        
        scene_final = os.path.join(TEMP_DIR, f"scene_{scene_id}_final.mp4")
        run_command([
            "ffmpeg", "-y", "-i", scene_video_no_audio, "-i", scene_audio,
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", scene_final
        ])
        
        scene_video_files.append(scene_final)

    # 2. Match all scenes into one final video
    print("\n🎬 Final Assembly of all scenes...")
    final_list_file = os.path.join(TEMP_DIR, "final_list.txt")
    with open(final_list_file, "w") as f:
        for s in scene_video_files:
            f.write(f"file '{os.path.abspath(s)}'\n")
            
    final_output = os.path.join(OUTPUT_VIDEO_DIR, "synced_rebirth_story.mp4")
    run_command([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_list_file,
        "-c", "copy", final_output
    ])

    print(f"\n✅ SUCCESS! Perfected synced video saved to: {final_output}")
    print("🧹 Cleaning up temp files...")

if __name__ == "__main__":
    main()
