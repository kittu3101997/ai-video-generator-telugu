import streamlit as st
import requests
import os
import tempfile
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip

st.set_page_config(page_title="AI Short Video Generator - Krishna Rao", layout="wide")

st.title("AI Short Video Generator – Krishna Rao 🚀")
st.markdown("""
Create short videos with AI visuals, Telugu/English voice & music.  
**Important 2026 Update**: Free hosted text-to-video is no longer available on Hugging Face (all models return 404).  
Use local ComfyUI for unlimited free generations (reply 'local' for setup guide).
""")

# Inputs
prompt = st.text_area("Video Prompt", height=120, placeholder="A beautiful sunrise over Mumbai\nor అందమైన ముంబై సూర్యోదయం")
language_choice = st.selectbox("Voice Language", ["English", "Telugu"])
duration_sec = st.slider("Duration (seconds)", 5, 30, 10)

lang_code = 'en' if language_choice == "English" else 'te'
tld = 'co.in' if language_choice == "English" else 'com'

if st.button("Generate Video", type="primary"):

    if not prompt:
        st.error("Enter a prompt first!")
        st.stop()

    with st.spinner("Trying generation (may take time on free tier)..."):
        try:
            # Voiceover
            tts = gTTS(text=prompt, lang=lang_code, tld=tld)
            voice_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            tts.save(voice_path)

            # Attempt hosted HF (will likely fail with 404)
            st.info("Trying Hugging Face router (may return 404 - normal in 2026)")
            api_url = "https://router.huggingface.co/hf-inference/models/tencent/HunyuanVideo"  # Will 404
            headers = {"Authorization": f"Bearer {st.secrets.get('HF_TOKEN', '')}"}
            payload = {"inputs": prompt, "parameters": {"num_frames": 24}}

            response = requests.post(api_url, headers=headers, json=payload, timeout=300)

            if response.status_code == 200:
                # Success path (rare)
                video_bytes = response.content
                video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
            else:
                st.warning("Hosted T2V not available (404 error - common now).")
                st.info("Switch to local ComfyUI for unlimited free use. Reply 'local' for code/setup!")
                # Stop here or use placeholder video if you want
                st.stop()

            # Extend video + add audio (same as before)
            base_video = VideoFileClip(video_path)
            extended = concatenate_videoclips([base_video] * (duration_sec // int(base_video.duration) + 2)).subclip(0, duration_sec)

            voice_audio = AudioFileClip(voice_path).subclip(0, duration_sec)

            music_url = "https://www.bensound.com/bensound-music/bensound-ukulele.mp3"
            music_bytes = requests.get(music_url).content
            music_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            with open(music_path, "wb") as f:
                f.write(music_bytes)

            music_audio = AudioFileClip(music_path).subclip(0, duration_sec).volumex(0.3)

            final_audio = CompositeAudioClip([voice_audio, music_audio])
            final_video = extended.set_audio(final_audio)

            final_path = "viral_video.mp4"
            final_video.write_videofile(final_path, codec="libx264", audio_codec="aac")

            st.success("Video Ready! (If you see this - hosted worked! Rare)")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("Download", f, "viral_video.mp4")

            # Cleanup
            os.unlink(voice_path)
            os.unlink(video_path)
            os.unlink(music_path)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("This is likely due to no free T2V models on Hugging Face serverless in 2026.")

st.caption("For unlimited: Use local ComfyUI + Wan/LTX models. Reply 'local' for full code!")
