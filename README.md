# Manhwa Generation (Script to Video)

A sophisticated system to transform scripts and stories into **Scene-Synced Manhwa Videos**. This tool handles AI text-to-speech (TTS), automatic image distribution, and cinematic zoom effects to create engaging webtoon/manhwa content for YouTube.

---

## 🎨 Features

*   **Scene-Level Synchronization:** Merges audio clips and corresponding image sequences per scene based on a `story_config.json`.
*   **Cinematic Zoom (ZoomPan):** Automatically applies variable zoom effects to static images to create dynamic video motion.
*   **Advanced TTS Integration:** Supports various TTS engines (including edge-tts and assemblyai) for voices that match the story's tone.
*   **Final Assembly:** Merges multiple scene clips, adds background audio, and performs a final concat of all story parts into a single `.mp4`.
*   **Auto-Fallback:** If images for a specific scene are missing, the tool intelligently falls back to related styles or placeholder assets.

---

## 🚀 Quick Start (Automated Setup)

Run the following command to set up the environment, install audio/video processing dependencies, and prepare the project structure:

```bash
chmod +x setup.sh
./setup.sh
```

---

## 📂 Usage

### 1. Configure Your Story (`story_config.json`)
Define your scenes, text, and expected prompt IDs in the config file.

### 2. Prepare Images
Ensure the `image_gen` suite has generated the matching images in its `output/` folder and that `manhwa_gen` is located as a sibling directory.

### 3. Generate Video
To create the final synced video from your script:
```bash
source audio_env/bin/activate
python video_maker_v2.py
```

---

## 📁 File Structure

*   `video_maker_v2.py`: Main entry point for synced video production.
*   `tts.py`: Audio generation module (Text-to-Speech).
*   `story_config.json`: Master configuration for scenes and prompts.
*   `video_generated/`: Final output location for produced stories.
*   `temp_assembly/`: Workfolder for intermediate scene clips.

---

*Authored and Maintained for Jatin Mudiraj.*
*Powered by Antigravity AI.*
