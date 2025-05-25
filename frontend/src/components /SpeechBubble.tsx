import React, { useState } from "react";

interface SpeechBubbleProps {
  text: string;
  isUser: boolean;
}

const SpeechBubble: React.FC<SpeechBubbleProps> = ({ text, isUser }) => {
  const [showFull, setShowFull] = useState(false);

  // Show first sentence followed by "..."
  const firstSentence = text.split(/(?<=[.?!])\s/)[0] + "...";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        onClick={() => setShowFull(true)}
        className={`cursor-pointer px-4 py-2 my-2 max-w-sm rounded-lg text-sm shadow-md ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-700 text-white"
        }`}
      >
        {firstSentence}
      </div>

      {showFull && (
        <div className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div className="bg-white text-black p-6 rounded-lg max-w-2xl max-h-[80vh] overflow-y-auto relative shadow-lg">
            <button
              onClick={() => setShowFull(false)}
              className="absolute top-2 right-4 text-gray-700 text-2xl font-bold"
            >
              &times;
            </button>
            <pre className="whitespace-pre-wrap text-base">{text}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default SpeechBubble;
