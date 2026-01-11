import streamlit as st
import requests
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
import os
import tempfile

st.title("AI Video Generator by Krishna")
st.markdown("Create short viral videos! Enter prompt → choose voice (English/Telugu) → select duration → get video with AI visuals, voiceover & music 🚀")

# User inputs
prompt = st.text_input("Enter your video prompt", 
                       placeholder="e.g., 'A futuristic city at night' or 'అందమైన తెలుగు గ్రామం సూర్యోదయం'")

language_choice = st.selectbox("Voice Language", ["English", "Telugu"])
gender = st.selectbox("Voice Gender (note: gTTS uses default tone)", ["Male", "Female"])
seconds = st.slider("Video duration (seconds)", min_value=5, max_value=30, value=10)

# Language mapping
lang_code = 'en' if language_choice == "English" else 'te'
tld = 'co.in' if language_choice == "English" else 'com'  # Indian accent for English

if st.button("Generate Fantastic Video"):

    with st.spinner("Generating AI magic... (1-3 minutes depending on queue)"):
        try:
            # 1. Generate voiceover
            narration_text = prompt
            tts = gTTS(text=narration_text, lang=lang_code, tld=tld, slow=False)
            voice_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            tts.save(voice_path)

            # 2. Generate base video clip using Hugging Face free inference API
            api_url = "https://router.huggingface.co/hf-inference/models/cerspense/zeroscope_v2_576w"
            headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
            
            payload = {"inputs": prompt}
            response = requests.post(api_url, headers=headers, json=payload)

            if response.status_code != 200:
                st.error(f"Hugging Face API error: {response.status_code} - {response.text[:200]}")
                st.stop()

            video_bytes = response.content
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            with open(video_path, "wb") as f:
                f.write(video_bytes)

            # 3. Load and extend video to desired length
            base_video = VideoFileClip(video_path)
            if base_video.duration == 0:
                st.error("Generated video clip has zero duration. Try a different prompt.")
                st.stop()

            # Simple looping to reach desired length
            loop_count = max(1, int(seconds / base_video.duration) + 2)
            extended_clips = [base_video] * loop_count
            extended_video = concatenate_videoclips(extended_clips).subclip(0, seconds)

            # 4. Prepare audio
            voice_audio = AudioFileClip(voice_path)
            if voice_audio.duration > seconds:
                voice_audio = voice_audio.subclip(0, seconds)

            # 5. Add free background music (royalty-free upbeat track)
            music_url = "https://www.bensound.com/bensound-music/bensound-ukulele.mp3"
            music_response = requests.get(music_url)
            music_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            with open(music_path, "wb") as f:
                f.write(music_response.content)

            music_audio = AudioFileClip(music_path).subclip(0, seconds).volumex(0.3)  # background volume

            # Combine voice + music
            combined_audio = CompositeAudioClip([voice_audio.set_start(0), music_audio.set_start(0)])

            # 6. Final video
            final_video = extended_video.set_audio(combined_audio)
            final_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            final_video.write_videofile(final_path, codec="libx264", audio_codec="aac", logger=None)

            # Cleanup temporary files
            for path in [voice_path, video_path, music_path]:
                if os.path.exists(path):
                    os.unlink(path)

            # Show success
            st.success("Video generated successfully! 🎉")
            st.video(final_path)

            # Download button
            with open(final_path, "rb") as f:
                st.download_button(
                    label="Download Video",
                    data=f,
                    file_name="viral_ai_video.mp4",
                    mime="video/mp4"
                )

            # Final cleanup
            os.unlink(final_path)

        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
            st.info("Common fixes: Check HF_TOKEN in secrets, try simpler prompt, or wait 1-2 min (free API queue)")
