import React, { useRef, useState } from "react";
import { useReactMediaRecorder } from "react-media-recorder";


const AudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);

  const handleStart = async () => {
    const res = await fetch("http://localhost:8000/start-transcription/", {
      method: "POST"
    });
    const json = await res.json();
    console.log(json.status);
    setIsRecording(true);
  };

  const handleStop = async () => {
    const res = await fetch("http://localhost:8000/stop-transcription/", {
      method: "POST"
    });
    const json = await res.json();
    console.log(json.status);
    setIsRecording(false);
  };

  return (
    <div>
      <h2>🎙️ Debate Bot Live Transcription</h2>
      <button onClick={isRecording ? handleStop : handleStart}>
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>
    </div>
  );
};

export default AudioRecorder;
