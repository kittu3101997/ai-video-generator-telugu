import streamlit as st
import requests
import json
import time
import os
import tempfile
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

# CONFIG: Change if ComfyUI runs on different port/host (e.g., remote VPS)
COMFYUI_URL = "http://127.0.0.1:8188"

# PASTE YOUR SAVED COMFYUI WORKFLOW HERE (API format JSON)
# Get it: Run ComfyUI → load LTX-Video/Wan workflow → Queue → Right-click → Save (API Format)
COMFY_WORKFLOW = {}  # ← REPLACE WITH YOUR REAL JSON (100+ lines typical)

st.title("Unlimited Local AI Video Generator - Krishna Rao 💰")
st.markdown("""
**100% FREE & UNLIMITED** - Local ComfyUI backend (no Hugging Face needed!)  
Models: LTX-Video (fast) or Wan 2.1/2.2 (high quality)  
**Run ComfyUI locally first!** Reply 'setup help' if stuck.
""")

prompt = st.text_area("Prompt (English or Telugu)", placeholder="A beautiful Telugu village sunrise with flying kites")
language = st.selectbox("Voice Language", ["English", "Telugu"])
duration_sec = st.slider("Duration (seconds)", 5, 30, 10)

if st.button("Generate Video (Unlimited Local) 🚀"):

    if not COMFY_WORKFLOW:
        st.error("Workflow JSON is empty! Paste your ComfyUI API workflow.")
        st.stop()

    with st.spinner("Generating locally via ComfyUI... (1-5 min depending on GPU)"):
        try:
            # Prepare workflow with user prompt
            workflow = json.loads(json.dumps(COMFY_WORKFLOW))
            # Update prompt node (change '3' to your actual node ID if different)
            for node_id, node in workflow.items():
                if "text" in node.get("inputs", {}) and "prompt" in node["inputs"]["text"].lower():
                    node["inputs"]["text"] = prompt
                    break

            # Queue in ComfyUI
            queue_resp = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
            queue_resp.raise_for_status()
            prompt_id = queue_resp.json()["prompt_id"]

            # Poll history
            history = None
            progress = st.progress(0)
            for i in range(180):  # ~6 min max
                hist = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
                if hist.status_code == 200 and hist.json().get(prompt_id):
                    history = hist.json()[prompt_id]
                    progress.progress(100)
                    break
                time.sleep(2)
                progress.progress(min((i + 1) / 180, 1))

            if not history:
                st.error("Timeout - check ComfyUI console/GPU.")
                st.stop()

            # Get video filename from output node (adjust if your workflow differs)
            output_node = list(history["outputs"].values())[-1]
            video_filename = output_node.get("images", [{}])[0].get("filename") or \
                             output_node.get("files", [{}])[0].get("filename")

            video_url = f"{COMFYUI_URL}/view?filename={video_filename}&type=output"
            video_data = requests.get(video_url).content

            video_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            with open(video_path, "wb") as f:
                f.write(video_data)

            # Voiceover + Music + Edit (same as before)
            lang_code = 'te' if language == "Telugu" else 'en'
            tts = gTTS(text=prompt, lang=lang_code, slow=False)
            voice_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
            tts.save(voice_path)

            music_url = "https://www.bensound.com/bensound-music/bensound-ukulele.mp3"
            music_data = requests.get(music_url).content
            music_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
            with open(music_path, "wb") as f:
                f.write(music_data)

            base_video = VideoFileClip(video_path)
            target_dur = duration_sec
            if base_video.duration < target_dur:
                loops = int(target_dur / base_video.duration) + 1
                base_video = concatenate_videoclips([base_video] * loops).subclip(0, target_dur)

            voice_audio = AudioFileClip(voice_path).subclip(0, target_dur)
            music_audio = AudioFileClip(music_path).subclip(0, target_dur).volumex(0.3)

            final_audio = CompositeAudioClip([voice_audio.set_start(0), music_audio.set_start(0)])
            final_video = base_video.set_audio(final_audio)

            final_path = "viral_video.mp4"
            final_video.write_videofile(final_path, codec="libx264", audio_codec="aac")

            st.success("Video Generated Locally! Unlimited & Free 🎉")
            st.video(final_path)

            with open(final_path, "rb") as f:
                st.download_button("Download MP4", f, file_name="krishna_viral_video.mp4")

            # Cleanup
            for p in [video_path, voice_path, music_path]:
                if os.path.exists(p):
                    os.unlink(p)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Ensure ComfyUI is running! Check setup guide below.")

st.markdown("---")
st.subheader("Local Setup Guide (Free & Unlimited)")
st.markdown("""
1. Download ComfyUI: https://github.com/comfyanonymous/ComfyUI (portable version easy)
2. Install custom nodes via Manager: ComfyUI-LTXVideo, Wan wrappers, HunyuanVideo
3. Download models free from Hugging Face: LTX-Video (fastest), Wan 2.1/2.2 (quality)
4. Create T2V workflow → Save as API JSON → paste into COMFY_WORKFLOW above
5. Run ComfyUI: python main.py
6. Run this app: streamlit run app.py
""")
st.caption("Start with LTX-Video for speed. Scale to earn lakhs: Custom Telugu videos, bulk Reels!")
