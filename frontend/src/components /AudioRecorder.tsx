import React, { useRef, useState } from "react";

const AudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState("");
  const socketRef = useRef<WebSocket | null>(null);

  const connectWebSocket = () => {
    const socket = new WebSocket("ws://localhost:8766");
    socketRef.current = socket;

    socket.onopen = () => {
      console.log("✅ WebSocket connected");
      setIsConnected(true);
      setIsConnecting(false);
    };

    socket.onmessage = (event) => {
      setTranscript((prev) => prev + " " + event.data);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
      setIsConnected(false);
    };

    socket.onclose = () => {
      console.log("❌ WebSocket disconnected");
      setIsConnected(false);
    };
  };

  const handleStart = async () => {
    setIsConnecting(true);

    const res = await fetch("http://localhost:8000/start-transcription/", {
      method: "POST",
    });
    const json = await res.json();
    console.log("Server:", json.status);

    connectWebSocket();
    setIsRecording(true);
  };

  const handleStop = async () => {
    const res = await fetch("http://localhost:8000/stop-transcription/", {
      method: "POST",
    });
    const json = await res.json();
    console.log("Server:", json.status);

    setIsRecording(false);
    socketRef.current?.close();

    await fetch("http://localhost:8000/final-speech/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ side: "Affirmative" }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("🧠 GPT Response:", data.speech);
      })
      .catch((err) => {
        console.error("❌ GPT generation failed:", err);
      });
  };

  return (
    <div style={{ padding: "1rem" }}>
      <h2>🎙️ Debate Bot Live Transcription</h2>

      <button
        onClick={isRecording ? handleStop : handleStart}
        disabled={isConnecting}
        style={{
          padding: "0.6rem 1rem",
          fontWeight: "bold",
          backgroundColor: isRecording ? "#e74c3c" : "#2ecc71",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
        }}
      >
        {isConnecting
          ? "⏳ Connecting..."
          : isRecording
          ? "Stop Recording"
          : "Start Recording"}
      </button>

      <div style={{ marginTop: "1rem" }}>
        <strong>Status:</strong>{" "}
        {isConnecting
          ? "Connecting to server..."
          : isRecording
          ? "Recording..."
          : "Idle"}
      </div>

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
    </div>
  );
};

export default AudioRecorder;