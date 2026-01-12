import streamlit as st
import requests
import os
import tempfile
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

st.set_page_config(page_title="AI Short Video Generator", layout="wide")

st.title("AI Short Video Generator – Krishna Rao 🚀")
st.markdown("""
**Create viral short videos instantly!**  
Prompt → Voice (English/Telugu) → Duration → AI Video + Music  
Free tier only (Hugging Face Inference Router – limited models in 2026)
""")

# ── Inputs ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    prompt = st.text_area(
        "Video Prompt (English or Telugu)",
        height=120,
        placeholder="Examples:\nA beautiful sunrise over Mumbai skyline\nఅందమైన ముంబై ఆకాశం మీద సూర్యోదయం",
        key="prompt"
    )

with col2:
    language_choice = st.selectbox("Voice Language", ["English", "Telugu"], index=0)
    duration_sec = st.slider("Duration (seconds)", 5, 30, 10, step=5)

# Language settings
lang_code = 'en' if language_choice == "English" else 'te'
tld = 'co.in' if language_choice == "English" else 'com'

# Generate button
if st.button("✨ Generate Video", type="primary", use_container_width=True):

    if not prompt.strip():
        st.error("Please enter a prompt!")
        st.stop()

    with st.spinner("Generating... (can take 1–8 minutes on free tier)"):
        try:
            # ── 1. Voiceover (gTTS - free & unlimited) ─────────────────────────
            tts = gTTS(text=prompt, lang=lang_code, tld=tld, slow=False)
            voice_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            tts.save(voice_path)

            # ── 2. Text-to-Video - 2026 Hugging Face Router attempt ───────────
            # Current best hope model (most likely to be hosted in Jan 2026)
            # If 404 → model is not on free inference → need local solution
            api_url = "https://router.huggingface.co/hf-inference/models/tencent/HunyuanVideo"

            headers = {
                "Authorization": f"Bearer {st.secrets.get('HF_TOKEN', '')}",
                "Content-Type": "application/json"
            }

            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_frames": 25,
                    "num_inference_steps": 30,
                    "height": 320,
                    "width": 576,
                    "guidance_scale": 7.5
                }
            }

            st.info("Trying latest available model: tencent/HunyuanVideo...")

            response = requests.post(api_url, headers=headers, json=payload, timeout=300)

            if response.status_code != 200:
                error_msg = response.text[:400] if response.text else "No response body"
                st.error(f"Hugging Face API Error {response.status_code}: {error_msg}")

                if "404" in str(response.status_code):
                    st.warning("""
**404 Not Found - Common in 2026 for text-to-video models**
Most classic T2V models are no longer free on serverless inference.

**Solutions:**
1. Try alternative model below (edit api_url in code):
   • tencent/HunyuanVideo-1.5
   • Lightricks/LTX-Video
   • wan-ai/Wan2.1-T2V (if hosted)

2. **Best free unlimited solution** → Run locally with ComfyUI + open-source models
   (RTX 3060+ GPU or rent Vast.ai pod ~₹2000–5000/month unlimited)

Reply with "local" if you want ComfyUI-based code!
                    """)
                st.stop()

            # ── Save generated video ───────────────────────────────────────
            video_bytes = response.content
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            with open(video_path, "wb") as f:
                f.write(video_bytes)

            # ── 3. Extend video duration by looping ──────────────────────────
            base_clip = VideoFileClip(video_path)
            if base_clip.duration <= 0:
                st.error("Generated clip has zero duration. Try different prompt.")
                st.stop()

            loops = int(duration_sec / base_clip.duration) + 2
            extended = concatenate_videoclips([base_clip] * loops).subclip(0, duration_sec)

            # ── 4. Audio preparation ─────────────────────────────────────────
            voice_audio = AudioFileClip(voice_path).subclip(0, duration_sec)

            # Free royalty-free upbeat music
            music_url = "https://www.bensound.com/bensound-music/bensound-ukulele.mp3"
            music_bytes = requests.get(music_url, timeout=15).content
            music_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            with open(music_temp, "wb") as f:
                f.write(music_bytes)

            music_audio = AudioFileClip(music_temp).subclip(0, duration_sec).volumex(0.3)

            final_audio = CompositeAudioClip([voice_audio.set_start(0), music_audio.set_start(0)])

            # ── 5. Final video ───────────────────────────────────────────────
            final_video = extended.set_audio(final_audio)
            final_path = "generated_video.mp4"
            final_video.write_videofile(final_path, codec="libx264", audio_codec="aac", logger=None)

            # Cleanup
            for p in [voice_path, video_path, music_temp]:
                if os.path.exists(p):
                    try:
                        os.unlink(p)
                    except:
                        pass

            # ── Success display ──────────────────────────────────────────────
            st.success("Video generated successfully! 🎉")
            st.video(final_path)

            with open(final_path, "rb") as f:
                st.download_button(
                    "Download MP4",
                    f,
                    file_name="krishna_ai_viral_video.mp4",
                    mime="video/mp4"
                )

        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.info("Most likely: Model not available on free inference or token issue")

st.markdown("---")
st.caption("2026 note: Free serverless text-to-video is very limited. Local ComfyUI is the real free unlimited path. Reply 'local' for that version!")
