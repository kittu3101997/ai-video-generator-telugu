import streamlit as st
import requests
from gtts import gTTS
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.audio.CompositeAudioClip import CompositeAudioClip
import os
import tempfile


st.title("AI Video Generator by Krishna Rao")
st.markdown("Enter a prompt, choose voice options, duration, and get a viral-ready video with AI visuals, voiceover, and music!")

prompt = st.text_input("Enter your video prompt (e.g., 'A futuristic city at night' or in Telugu: 'రాత్రి భవిష్యత్ నగరం')")
language_choice = st.selectbox("Voice Language", ["English", "Telugu"])
gender = st.selectbox("Voice Gender", ["Male", "Female"])  # gTTS uses defaults; Telugu is neutral/male-leaning
seconds = st.slider("How many seconds? (5-30)", min_value=5, max_value=30, value=10)

# Map to gTTS lang code
lang_code = 'en' if language_choice == "English" else 'te'

# For accents: Indian flavor
tld = 'co.in' if language_choice == "English" else 'com'

if st.button("Generate Fantastic Video"):
    with st.spinner("Generating AI magic with selected voice... This may take 1-2 minutes!"):
        # Step 1: Generate voiceover
        narration_text = prompt  # Use prompt as narration; translate if needed later
        tts = gTTS(text=narration_text, lang=lang_code, tld=tld, slow=False)
        voice_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        tts.save(voice_path)

        # Step 2: Generate base video using Hugging Face API
        api_url = "https://api-inference.huggingface.co/models/cerspense/zeroscope_v2_576w"  # Free text-to-video
        headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
        payload = {"inputs": prompt}
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            st.error(f"API error: {response.text}. Check token or try later.")
            st.stop()
        
        video_bytes = response.content
        video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        with open(video_path, "wb") as f:
            f.write(video_bytes)

        # Load base video (~3-5 sec clip)
        base_video = VideoFileClip(video_path)

        # Step 3: Extend to match seconds
        duration = base_video.duration
        if duration == 0:
            st.error("Generated video is empty. Try a different prompt.")
            st.stop()
        loop_count = max(1, seconds // int(duration)) + 1
        extended_video = concatenate_videoclips([base_video] * loop_count).subclip(0, seconds)

        # Step 4: Add voiceover
        voice_audio = AudioFileClip(voice_path)
        if voice_audio.duration > seconds:
            voice_audio = voice_audio.subclip(0, seconds)
        # No gender swap in gTTS; for advanced, use HF models later

        # Step 5: Add free background music
        music_url = "https://www.bensound.com/bensound-music/bensound-ukulele.mp3"  # Royalty-free
        music_response = requests.get(music_url)
        music_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        with open(music_path, "wb") as f:
            f.write(music_response.content)
        music_audio = AudioFileClip(music_path).subclip(0, seconds).volumex(0.3)

        # Combine audio
        combined_audio = CompositeAudioClip([voice_audio.set_start(0), music_audio.set_start(0)])

        # Final video
        final_video = extended_video.set_audio(combined_audio)
        final_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        final_video.write_videofile(final_path, codec="libx264", audio_codec="aac")

        # Cleanup
        os.unlink(voice_path)
        os.unlink(video_path)
        os.unlink(music_path)

    st.success("Your amazing video is ready! 🎉")
    st.video(final_path)
    with open(final_path, "rb") as f:
        st.download_button("Download Video", f, file_name="viral_video.mp4")
    os.unlink(final_path)
