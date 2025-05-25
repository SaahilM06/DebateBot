import React, { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "bot";
  content: string;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", content: "Hi! I'm DebateBot. What would you like to debate today?" }
  ]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const sendMessage = () => {
    if (input.trim() === "") return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: input },
      { role: "bot", content: `Interesting point! Here's a counter...` }, // placeholder response
    ]);
    setInput("");
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="p-4 border-b border-gray-700 text-lg font-semibold bg-gray-800">
        DebateBot
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-md px-4 py-2 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 text-white"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 bg-gray-800 p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 rounded-lg bg-gray-700 p-2 text-white focus:outline-none"
            placeholder="Type your message..."
          />
          <button
            type="submit"
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat;
