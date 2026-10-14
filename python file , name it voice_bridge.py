
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


def handle_question():
    print("\nRecording for 5 seconds. Speak now!")

    recording = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    if np.max(np.abs(recording.astype(np.int32))) < 100:
        print("Recording is very quiet. Please check your microphone.")
        return

    wav_path = "user_audio.wav"
    write(wav_path, SAMPLE_RATE, recording)

    print("Sending audio to ESP32...")

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
        response.raise_for_status()

        data = response.json()
        answer = data.get("text", "").replace("*", "").strip()

        if not answer:
            print("No answer returned:", data)
            return

        print("\n=== GEMINI ANSWER ===")
        print(answer)

        print("Speaking through your default audio output...")
        speaker.say(answer)
        speaker.runAndWait()

    except requests.exceptions.RequestException as error:
        print("Request failed:", error)
        print("Check ESP32 power, Wi-Fi, IP address and Gemini connection.")

    except Exception as error:
        print("Error:", error)


def main():
    print("=== ESP32 GEMINI VOICE ASSISTANT ===")
    print("Connect your earbuds and ensure the ESP32 is running.")
    print("The assistant will keep listening until you stop it.")
    print("Press Ctrl+C in this terminal to stop.\n")

    while True:
        try:
            handle_question()
            print("\nPreparing for your next question...")
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nVoice assistant stopped.")
            break

        except Exception as error:
            print("Unexpected error:", error)
            time.sleep(2)


if __name__ == "__main__":
    main()
