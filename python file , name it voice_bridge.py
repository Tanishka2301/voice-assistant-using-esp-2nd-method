import base64
import time

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import requests
import pyttsx3

ESP32_URL = "http://10.185.198.181:8000/audio"

SAMPLE_RATE = 16000
RECORD_SECONDS = 5

speaker = pyttsx3.init()


def main():
    print("\n=== ESP32 GEMINI VOICE ASSISTANT ===")
    print("Available audio devices:")
    print(sd.query_devices())

    input("\nConnect your earbuds and press Enter to record...")

    print("Recording for 5 seconds. Speak now!")
    recording = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    if np.max(np.abs(recording.astype(np.int32))) < 100:
        print("Warning: recording is very quiet or silent.")

    wav_path = "user_audio.wav"
    write(wav_path, SAMPLE_RATE, recording)

    print("Recording saved. Sending audio to ESP32...")

    with open(wav_path, "rb") as audio_file:
        encoded_audio = base64.b64encode(
            audio_file.read()
        ).decode("ascii")

    try:
        response = requests.post(
            ESP32_URL,
            json={"audio": encoded_audio},
            timeout=180
        )

        print("ESP32 HTTP status:", response.status_code)
        print("ESP32 response:", response.text)
        response.raise_for_status()

        data = response.json()
        answer = data.get("text", "")
        answer = answer.replace("*", "")
        answer = answer.replace("#", "")
        answer = answer.replace("_", "")
        answer = answer.replace("'", "")
        if not answer:
            print("No answer returned:", data)
            return

        print("\n=== GEMINI ANSWER ===")
        print(answer)

        print("\nSpeaking through the Windows default output...")
        speaker.say(answer)
        speaker.runAndWait()

    except requests.exceptions.RequestException as error:
        print("Connection/request failed:", error)
        print("Check that the ESP32 is powered on,")
        print("both devices use the same Wi-Fi,")
        print("and the ESP32 IP address is correct.")


if __name__ == "__main__":
    main()
