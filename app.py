import streamlit as st
import requests
import os
import tempfile
import time
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

st.set_page_config(page_title="AI Short Video Generator", layout="wide")

st.title("AI Short Video Generator – Krishna Rao 🚀")
st.markdown("""
Create viral-ready short videos instantly!  
Enter your prompt → choose language → select duration → get AI-generated video with voiceover & music.  
**100% free to use** (powered by free-tier Hugging Face Inference)
""")

# ── User inputs ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    prompt = st.text_area(
        "Video Prompt (English or Telugu)",
        height=100,
        placeholder="Examples:\nA beautiful sunrise over a Telugu village\nఅందమైన తెలుగు గ్రామంలో సూర్యోదయం",
        key="prompt"
    )

with col2:
    language_choice = st.selectbox("Voice Language", ["English", "Telugu"], index=0)
    duration = st.slider("Duration (seconds)", 5, 30, 10, step=5)

# Language settings
lang_code = 'en' if language_choice == "English" else 'te'
tld = 'co.in' if language_choice == "English" else 'com'  # Indian accent for English

# Generate button
if st.button("✨ Generate Fantastic Video", type="primary", use_container_width=True):

    if not prompt.strip():
        st.error("Please enter a prompt first!")
        st.stop()

    with st.spinner("Generating AI video... (1–5 minutes depending on queue)"):
        try:
            # ── 1. Voiceover ──────────────────────────────────────────────────────
            tts = gTTS(text=prompt, lang=lang_code, tld=tld, slow=False)
            voice_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            tts.save(voice_path)

            # ── 2. Text-to-Video using updated 2026 Hugging Face Router ──────────
            # Recommended model: damo-vilab/text-to-video-ms-1.7b (most reliable classic)
            # Alternative models you can try: "cerspense/zeroscope_v2_576w", "hotshot-xl/hotshot-xl"
            #api_url = "https://router.huggingface.co/hf-inference/models/tencent/HunyuanVideo"
            # OR
           api_url = "https://router.huggingface.co/hf-inference/models/Lightricks/LTX-Video"

            headers = {
                "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
                "Content-Type": "application/json"
            }

            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_frames": 24,           # ~3-4 second base clip
                    "num_inference_steps": 25,
                    "height": 320,
                    "width": 576,
                    "guidance_scale": 7.5
                }
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=180)

            if response.status_code != 200:
                error_text = response.text[:400]
                st.error(f"Hugging Face API Error {response.status_code}:\n{error_text}")
                st.info("Common fixes:\n• Check your HF_TOKEN in secrets\n• Wait 1-2 min (free tier queue)\n• Try simpler prompt")
                st.stop()

            video_bytes = response.content
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            with open(video_path, "wb") as f:
                f.write(video_bytes)

            # ── 3. Load & extend video to desired duration ───────────────────────
            base_clip = VideoFileClip(video_path)

            if base_clip.duration <= 0:
                st.error("Generated video clip has zero duration. Try a different prompt.")
                st.stop()

            # Loop the clip enough times to exceed requested duration, then cut
            loops_needed = int(duration / base_clip.duration) + 2
            extended = concatenate_videoclips([base_clip] * loops_needed)
            extended = extended.subclip(0, duration)

            # ── 4. Prepare audio ─────────────────────────────────────────────────
            voice_audio = AudioFileClip(voice_path)
            if voice_audio.duration > duration:
                voice_audio = voice_audio.subclip(0, duration)

            # Free upbeat royalty-free music (Bensound - commercial safe)
            music_url = "https://www.bensound.com/bensound-music/bensound-ukulele.mp3"
            music_bytes = requests.get(music_url, timeout=15).content
            music_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            with open(music_temp, "wb") as f:
                f.write(music_bytes)

            music_audio = AudioFileClip(music_temp).subclip(0, duration).volumex(0.3)

            # Combine
            final_audio = CompositeAudioClip([voice_audio.set_start(0), music_audio.set_start(0)])

            # ── 5. Final video ───────────────────────────────────────────────────
            final_video = extended.set_audio(final_audio)

            final_path = "generated_viral_video.mp4"
            final_video.write_videofile(final_path, codec="libx264", audio_codec="aac", logger=None)

            # Cleanup temporary files
            for path in [voice_path, video_path, music_temp]:
                if os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass

            # ── Success ──────────────────────────────────────────────────────────
            st.success("Your video is ready! 🎉")
            st.video(final_path)

            with open(final_path, "rb") as f:
                st.download_button(
                    label="Download Video (MP4)",
                    data=f,
                    file_name="krishna_ai_viral_video.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Unexpected error occurred:\n{str(e)}")
            st.info("Tips:\n• Make sure HF_TOKEN is correctly set in Streamlit secrets\n• Try shorter / simpler prompt\n• Wait a few minutes and retry")

# Footer
st.markdown("---")
st.caption("Powered by Hugging Face Inference Router • gTTS • MoviePy • 100% free tier • Built for viral Telugu & English content • January 2026")
