import whisper

def transcribe_audio(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

if __name__ == "__main__":
    print(transcribe_audio("audio/A one minute TEDx Talk for the digital age  Woody Roseland  TEDxMileHigh.mp3"))


