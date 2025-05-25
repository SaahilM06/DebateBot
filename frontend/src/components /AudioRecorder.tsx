import React, { useRef, useState } from "react";

const AudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState<"Idle" | "Connecting" | "Recording">("Idle");
  const [transcript, setTranscript] = useState("");
  const socketRef = useRef<WebSocket | null>(null);

  const connectWebSocket = () => {
    const socket = new WebSocket("ws://localhost:8000/ws");
    socketRef.current = socket;

    socket.onmessage = (event) => {
      setTranscript((prev) => prev + " " + event.data);
    };

    socket.onopen = () => {
      console.log("✅ WebSocket connected");
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    socket.onclose = () => {
      console.log("❌ WebSocket disconnected");
    };
  };

  const handleStart = async () => {
    setStatus("Connecting");
  
    // Fire & forget backend + WS
    fetch("http://localhost:8000/start-transcription/", { method: "POST" }).catch(console.error);
    connectWebSocket();
  
    // ✅ Independent 5-second UI update regardless of backend
    setTimeout(() => {
      setStatus("Recording");
      setIsRecording(true);
    }, 5000);
  };
  

  const handleStop = async () => {
    setIsRecording(false);
    setStatus("Idle");
    socketRef.current?.close();

    await fetch("http://localhost:8000/stop-transcription/", { method: "POST" });

    const res = await fetch("http://localhost:8000/final-speech/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ side: "Affirmative" }),
    });
    const data = await res.json();
    console.log("🧠 GPT Response:", data.speech);
  };

  return (
    <div style={{ padding: "1rem" }}>
      <h2>🎙️ Debate Bot Live Transcription</h2>

      <button
        onClick={isRecording ? handleStop : handleStart}
        disabled={status === "Connecting"}
        style={{
          padding: "0.6rem 1rem",
          fontWeight: "bold",
          backgroundColor:
            status === "Connecting"
              ? "#f39c12"
              : isRecording
              ? "#e74c3c"
              : "#2ecc71",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: status === "Connecting" ? "not-allowed" : "pointer",
          transition: "background-color 0.3s",
        }}
      >
        {status === "Connecting"
          ? "⏳ Connecting..."
          : isRecording
          ? "Stop Recording"
          : "Start Recording"}
      </button>

      <div style={{ marginTop: "1rem" }}>
        <strong>Status:</strong> {status}
      </div>

      {status === "Connecting" && (
        <div style={{ marginTop: "10px", color: "#f39c12", fontWeight: "bold" }}>
          ⏳ Whisper model warming up...
        </div>
      )}

      {status === "Recording" && (
        <div style={{ display: "flex", gap: "4px", marginTop: "10px", height: "30px" }}>
          {Array.from({ length: 10 }).map((_, i) => (
            <div
              key={i}
              style={{
                width: "4px",
                height: `${10 + Math.random() * 20}px`,
                backgroundColor: "#2ecc71",
                animation: "pulse 1s infinite",
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
        </div>
      )}

      <div
        style={{
          marginTop: "1rem",
          border: "1px solid #ccc",
          padding: "1rem",
          borderRadius: "5px",
          backgroundColor: "#f9f9f9",
          minHeight: "100px",
          whiteSpace: "pre-wrap",
        }}
      >
        <strong>Live Transcript:</strong>
        <br />
        {transcript || "Waiting for speech..."}
      </div>

      <style>
        {`
          @keyframes pulse {
            0% { transform: scaleY(1); }
            50% { transform: scaleY(2); }
            100% { transform: scaleY(1); }
          }
        `}
      </style>
    </div>
  );
};

export default AudioRecorder;
