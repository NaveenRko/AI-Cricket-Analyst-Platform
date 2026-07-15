from streamlit_mic_recorder import mic_recorder

audio = mic_recorder(
    start_prompt="🎤 Start Recording",
    stop_prompt="Stop",
    just_once=True
)

audio = audio["bytes"]