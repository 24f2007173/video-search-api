from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import os
import re

app = FastAPI()

class AskRequest(BaseModel):
    video_url: str
    topic: str

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

@app.post("/ask")
def ask(data: AskRequest):

    video_url = data.video_url
    topic = clean_text(data.topic)
    topic_words = topic.split()

    # Download English auto subtitles only
    subprocess.run([
        "yt-dlp",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        "-o", "subs.%(ext)s",
        video_url
    ])

    # Find subtitle file
    subtitle_file = None
    for file in os.listdir():
        if file.endswith(".vtt"):
            subtitle_file = file
            break

    if not subtitle_file:
        return {
            "timestamp": "00:00:00",
            "video_url": video_url,
            "topic": data.topic
        }

    timestamp = "00:00:00"

    with open(subtitle_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if "-->" in lines[i]:
            time_part = lines[i].split("-->")[0].strip()

            text_block = ""
            j = i + 1
            while j < len(lines) and "-->" not in lines[j]:
                text_block += " " + lines[j].strip()
                j += 1

            cleaned_block = clean_text(text_block)

            # Count how many topic words appear
            match_count = sum(1 for word in topic_words if word in cleaned_block)

            # If most words match (at least half)
            if match_count >= max(1, len(topic_words) // 2):
                timestamp = time_part.split(".")[0]
                break

    os.remove(subtitle_file)

    return {
        "timestamp": timestamp,
        "video_url": video_url,
        "topic": data.topic
    }