import whisper

def transcribe_audio(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

if __name__ == "__main__":
    print(transcribe_audio("/Users/saahi/Desktop/debate-bot/audio/NSDA Championship Winning Speech.mp3"))

