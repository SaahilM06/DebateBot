import React, { useRef, useState, useEffect } from "react";
import SpeechBubble from "./components /SpeechBubble";
import { TextBox } from '@syncfusion/ej2-inputs';
import './license';



const Dropdown = ({ options, onSelect, label }: { options: string[]; onSelect: (value: string) => void; label: string }) => {
 const [isOpen, setIsOpen] = useState(false);
 const [selected, setSelected] = useState<string | null>(null);


 const handleSelect = (option: string) => {
   setSelected(option);
   onSelect(option);
   setIsOpen(false);
 };


 const handleSubmit = async () => {
   if (!selected) {
     alert("Make a choice before submitting");
     return;
   }
   try {
     const response = await fetch("http://localhost:8000/submit-choice/", {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ choice: selected })
     });
     if (!response.ok) throw new Error("Failed to submit");
     const result = await response.json();
     alert(result.message);
     setSelected(null);
   } catch (error) {
     console.error("error", error);
   }
 };


 return (
   <div className="w-52 relative">
     <label className="text-white block mb-1">{label}</label>
     <div
       className="border border-gray-500 px-3 py-2 bg-gray-800 text-white cursor-pointer rounded-md"
       onClick={() => setIsOpen(!isOpen)}
     >
       {selected || "Select..."}
     </div>
     {isOpen && (
       <ul className="absolute z-10 mt-1 w-full bg-gray-800 text-white border border-gray-500 rounded-md shadow-lg">
         {options.map(option => (
           <li
             key={option}
             className="px-3 py-2 hover:bg-gray-700 cursor-pointer"
             onClick={() => handleSelect(option)}
           >
             {option}
           </li>
         ))}
       </ul>
     )}
     <button onClick={handleSubmit} className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded">
       Submit Choice
     </button>
   </div>
 );
};


const App = () => {
 const [isRecording, setIsRecording] = useState(false);
 const [status, setStatus] = useState("Idle");
 const [transcript, setTranscript] = useState("");
 const [gptResponse, setGptResponse] = useState("");
 type Message = {
  text: string;
  isUser: boolean;
};

const [messages, setMessages] = useState<Message[]>([]);
 const [file, setFile] = useState<File | null>(null);
 const [billFile, setBillFile] = useState<File | null>(null);
 const [hasStarted, setHasStarted] = useState(false);
 const [conversationId, setConversationId] = useState<string | null>(null);
 const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
 const [isSpeaking, setIsSpeaking] = useState(false);




 const [allConversations, setAllConversations] = useState<{ id: string; title: string }[]>([]);


 const socketRef = useRef<WebSocket | null>(null);

 const [isCrossExActive, setIsCrossExActive] = useState(false);
 const [crossTranscript, setCrossTranscript] = useState("");
 const [crossExHistory, setCrossExHistory] = useState<{ question: string; answer: string }[]>([]);
 const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
 const crossSocketRef = useRef<WebSocket | null>(null);

 const [showInstructionModal, setShowInstructionModal] = useState(false);
const [customInstruction, setCustomInstruction] = useState("");
const [showInitialInstructions, setShowInitialInstructions] = useState(true);



 useEffect(() => {
 const fetchConversations = async () => {
   const res = await fetch("http://localhost:8000/conversations/");
   const data = await res.json();
   setAllConversations(data.conversations);
 };
    fetchConversations();
 }, []);


 const sendCrossQuestion = async (questionText: string) => {
  const res = await fetch("http://localhost:8000/cross-response/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: questionText,
      history: crossExHistory,
    }),
  });

  const data = await res.json();
  const answer = data.answer;

  setCrossExHistory(prev => [...prev, { question: questionText, answer }]);
  setMessages(prev => [...prev, { text: questionText, isUser: true }, { text: answer, isUser: false }]);

  await fetch("http://localhost:8000/speak-instruction/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: answer }),
  });
};

const handleStartCrossEx = async () => {
  try {
    const start = await fetch("http://localhost:8000/start-crossref/", { method: "POST" });
    const startData = await start.json();
    console.log("▶️ CrossRef:", startData.status);

    const poll = async () => {
      const res = await fetch("http://localhost:8000/get-crossref-result/");
      const data = await res.json();

      if (data.ready) {
        console.log("✅ CrossRef data ready:", data);
        setMessages((prev) => [
          ...prev,
          { text: data.question, isUser: true },
          { text: data.answer, isUser: false }
        ]);
      } else {
        setTimeout(poll, 1000); // Try again in 1 second
      }
    };

    poll();
  } catch (err) {
    console.error("❌ CrossRef error:", err);
  }
};




const handleStopCrossEx = async () => {
  try {
    const res = await fetch("http://localhost:8000/stop-crossref/", {
      method: "POST",
    });
    const data = await res.json();
    console.log("⏹ CrossRef stopped:", data.status);
  } catch (err) {
    console.error("Failed to stop crossref:", err);
  }
};

  const loadConversation = async (id: string) => {
   setConversationId(null);
   setTranscript("");
   setGptResponse("");
   setHasStarted(false);
    const convoRes = await fetch(`http://localhost:8000/conversation/${id}`);
   const convoData = await convoRes.json();
   if (!convoData.error) {
     setConversationId(id);
     setActiveConversationId(id);
     setGptResponse(convoData.response || "");
     setHasStarted(convoData.hasStarted || false);
  
     setTranscript(convoData.transcript || "");
   }
 };
 


 const handleNewDebate = async () => {
   try {
     const res = await fetch("http://localhost:8000/new-conversation/", { method: "POST" });
     const data = await res.json();
     setConversationId(data.conversation_id);
     setIsRecording(false);
     setStatus("Idle");
     setTranscript("");
     setGptResponse("");
     setFile(null);
     setBillFile(null);
     setHasStarted(false);
     socketRef.current?.close();
     setMessages([]);



     const convoRes = await fetch("http://localhost:8000/conversations/");
     const updated = await convoRes.json();
     setAllConversations(updated.conversations);


   } catch (error) {
     console.error("Failed to create new conversation", error);
   }
 };


 const handleSideSelect = (side: string) => {
   console.log("User chose:", side);
 };


 const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
   const selectedFile = event.target.files?.[0];
   if (selectedFile) setFile(selectedFile);
 };


 const handleBillFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
   const selectedFile = event.target.files?.[0];
   if (selectedFile) setBillFile(selectedFile);
 };


 const handleSubmit = async () => {
   if (!file) return alert("Make a choice before submitting");
   const formData = new FormData();
   formData.append("file_upload", file);
   const res = await fetch("http://localhost:8000/file-choice/", { method: "POST", body: formData });
   const result = await res.json();
   alert(result.message);
   setFile(null);
 };


 const handleBillSubmit = async () => {
   if (!billFile) return alert("Upload your bill first.");
   const formData = new FormData();
   formData.append("file_upload", billFile);
   const res = await fetch("http://localhost:8000/bill-choice/", { method: "POST", body: formData });
   const result = await res.json();
   alert(result.message);
   setBillFile(null);
 };


 const handleVectorize = async () => {
  if (!conversationId) return alert("No conversation selected.");

  try {
    const res = await fetch(`http://localhost:8000/run-vectorize/${conversationId}`, {
      method: "POST",
    });
    const result = await res.json();

    if (result.message) {
      alert(result.message);
      setHasStarted(true);

      // Reload backend AFTER vectorization
      

      // Speak instruction
      /*
      await fetch("http://localhost:8000/speak-instruction/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: "Now, the Affirmative will begin. You have 3 minutes to give your speech. The opponent will respond after.",
        }),
      });
      */
      
      
    } else {
      alert("Error: " + result.error);
    }

  } catch (err: any) {
    console.error("Vectorize failed:", err);
    alert("Vectorize failed: " + err.message);
  }
};



 const handleStart = async () => {
   setStatus("Connecting");
   fetch("http://localhost:8000/start-transcription/", { method: "POST" }).catch(console.error);
   connectWebSocket();
   setTimeout(() => {
     setStatus("Recording");
     setIsRecording(true);
   }, 5000);

   const inputBox = new TextBox({
    placeholder: 'Enter your response here...',
  });
  inputBox.appendTo('#textbox-target');
 };


 const handleSkipTTS = async () => {
   try {
     const res = await fetch("http://localhost:8000/stop-tts/", { method: "POST" });
     const result = await res.json();
     console.log("⏹ TTS Stopped:", result.status);
     setIsSpeaking(false);
   } catch (error) {
     console.error("Failed to stop TTS:", error);
   }
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

  if (conversationId) {
    await fetch(`http://localhost:8000/save-transcript/${conversationId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript }),
    });
  }

  const check = await fetch(`http://localhost:8000/conversation/${conversationId}`);
  const updated = await check.json();

  const userMessage = updated.transcript || "";
  const botMessage = data.speech || "";

  setMessages((prev) => [
    ...prev,
    { text: userMessage, isUser: true },
    { text: botMessage, isUser: false },
  ]);
  setTranscript("");

  try {
    setIsSpeaking(true);
    await fetch("http://localhost:8000/start-tts/", { method: "POST" });
    console.log("TTS playback started.");
  } catch (error) {
    console.error("Failed to start TTS:", error);
  } finally {
    // Wait for 10s then mark TTS done
    setTimeout(() => {
      setIsSpeaking(false);
        
      /*
      fetch("http://localhost:8000/speak-instruction/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text:
            "Now, the cross examination will begin. The Affirmative will have one minute to question the Negative. Then the roles will be switched.",
        }),
      });
      */
    }, 10000);
  }
};



 const connectWebSocket = () => {
   if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
     console.log("⚠️ WebSocket already connected.");
     return;
   }
    const socket = new WebSocket("ws://localhost:8000/ws");
   socketRef.current = socket;
    socket.onopen = () => {
     console.log("✅ WebSocket connected");
   };
    socket.onmessage = (event) => {
     setTranscript((prev) => {
       const updated = prev + " " + event.data;
       if (conversationId) {
         fetch(`http://localhost:8000/save-transcript/${conversationId}`, {
           method: "POST",
           headers: { "Content-Type": "application/json" },
           body: JSON.stringify({ transcript: updated }),
         });
       }
       return updated;
     });
   };
    socket.onerror = (err) => console.error("WebSocket error:", err);
    socket.onclose = () => {
     console.log("❌ WebSocket disconnected");
   };
 };


 return (
   <div className="bg-gray-900 text-gray-100 flex h-screen">
     <aside className="w-72 bg-gray-800 p-4 flex flex-col justify-between">
       <div>
         <div className="flex justify-between items-center mb-6">
           <button className="p-2 hover:bg-gray-700 rounded-md">
             <span className="material-icons">menu</span>
           </button>
         </div>
         <button
           onClick={handleNewDebate}
           className="flex items-center w-full text-left py-2.5 px-4 rounded-md hover:bg-gray-700 mb-2"
         >
           <span className="material-icons mr-3">add_circle_outline</span>
           New Debate
         </button>

         <button
  onClick={() => setShowInitialInstructions(true)}
  className="flex items-center w-full text-left py-2.5 px-4 rounded-md hover:bg-gray-700 mb-2"
>
  <span className="material-icons mr-3">info</span>
  Instructions
</button>
         <h3 className="text-xs text-gray-400 uppercase font-semibold mb-3 px-4">Tools</h3>
         <nav className="space-y-1 mb-6">
           <a className="flex items-center py-2 px-4 rounded-md hover:bg-gray-700 text-sm" href="#">
             <span className="material-icons mr-3 text-blue-400">shield</span>
             Argument Checker
           </a>
         </nav>
         <h3 className="text-xs text-gray-400 uppercase font-semibold mb-3 px-4">Conversations</h3>
         <nav className="space-y-1">
         {allConversations.map((c) => (
 <div key={c.id} className="flex items-center justify-between">
   <button
     onClick={() => loadConversation(c.id)}
     className="block py-2 px-4 text-left rounded-md hover:bg-gray-700 text-sm truncate w-full"
   >
     {c.title}
   </button>
   <button
     onClick={async () => {
       const confirmed = window.confirm("Are you sure you want to delete this conversation?");
       if (!confirmed) return;


       try {
         const res = await fetch(`http://localhost:8000/conversation/${c.id}`, { method: "DELETE" });
         if (!res.ok) {
           alert("Failed to delete conversation.");
           return;
         }
         setAllConversations((prev) => prev.filter((conv) => conv.id !== c.id));
         if (conversationId === c.id) {
           setConversationId(null);
           setTranscript("");
           setGptResponse("");
           setHasStarted(false);
         }
       } catch (err) {
         console.error("Error deleting:", err);
         alert("Failed to delete conversation.");
       }
     }}
     className="ml-2 text-red-400 hover:text-red-600 text-sm"
   >
     ✕
   </button>
 </div>
))}


</nav>


       </div>
     </aside>
     <main className="flex-1 flex flex-col items-center justify-center p-6 overflow-y-auto">
       {(hasStarted || transcript || gptResponse) ? (
         <>
 <div className="w-full max-w-2xl space-y-3 mt-4 flex flex-col">

 {messages.map((msg, index) => (
  <div key={index} className={msg.isUser ? "self-end" : "self-start"}>
    <SpeechBubble text={msg.text} isUser={msg.isUser} />
  </div>
))}
</div>



 <div className="mt-4 flex justify-center">
   <button
     onClick={handleSkipTTS}


     className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded shadow-md"
   >
     ⏭ Skip Speech
   </button>
 </div>


         
           <div className="w-full max-w-3xl mt-auto sticky bottom-6">
             <h2 className="text-3xl font-semibold text-gray-300 mb-12 text-center">What topic shall we debate today?</h2>
             <div className="bg-gray-700 rounded-xl p-1 flex items-center shadow-xl">
               <div className="flex-grow bg-transparent p-3 text-gray-400 italic">Speak your debate topic or question...</div>
               <button
                 className={`${isRecording ? "bg-red-600" : "bg-green-600"} text-white p-3 rounded-lg ml-2`}
                 onClick={isRecording ? handleStop : handleStart}
               >
                 <span className="material-icons">{isRecording ? "stop" : "mic"}</span>
               </button>

               {!isCrossExActive ? (
  <button
    onClick={handleStartCrossEx}
    className="bg-purple-600 text-white px-4 py-2 rounded ml-2"
  >
    🎙 Start Cross-Ex
  </button>
) : (
  <button
    onClick={handleStopCrossEx}
    className="bg-red-600 text-white px-4 py-2 rounded ml-2"
  >
    ⏹ Stop Cross-Ex
  </button>

  
)}

             </div>
             <p className="text-xs text-gray-500 text-center mt-3">DebateBot can make mistakes. Consider checking important information.</p>
           </div>
         </>
       ) : (
         <div className="w-full max-w-3xl space-y-6 mb-auto">
           <Dropdown options={["Affirmative", "Negative"]} onSelect={handleSideSelect} label="Choose Your Side" />
           <p>Submit your reference speech here</p>
           <input type="file" onChange={handleFileChange} />
           <button onClick={handleSubmit} className="bg-blue-600 rounded px-4 py-1 mt-2">Submit Choice</button>
           <p className="mt-4">Submit your bill here</p>
           <input type="file" onChange={handleBillFileChange} />
           <button onClick={handleBillSubmit} className="bg-green-600 rounded px-4 py-1 mt-2">Submit Choice</button>
           <button onClick={handleVectorize} className="bg-purple-600 rounded px-4 py-1 mt-4">Process</button>
           {showInstructionModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white text-black rounded-lg p-6 w-96 shadow-lg">
      <h2 className="text-xl font-semibold mb-4">Instructions</h2>
      <div className="whitespace-pre-line border border-gray-300 rounded p-3 bg-gray-100 text-sm">
        {customInstruction}
      </div>
      <div className="mt-4 flex justify-end">
        <button
          onClick={() => setShowInstructionModal(false)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Close
        </button>
      </div>
      <div id="textbox-target" className="mt-4" />

    </div>
  </div>
)}

         </div>
       )}
     </main>

     {showInitialInstructions && (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
    <div className="bg-white text-black p-6 rounded-lg shadow-lg w-96">
      <h2 className="text-lg font-semibold mb-3">Welcome to DebateBot</h2>
      <p className="text-sm whitespace-pre-line">
        This is a live debate tool. Choose your side, submit the reference bill. After this, speak your argument for 3 minutes max after clicking the microphone. 
        The bot will respond for a max time of 3 min. After this start cross examination for 1 minute in real time
      </p>
      <div className="text-right mt-4">
        <button
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
          onClick={() => setShowInitialInstructions(false)}
        >
          Got it
        </button>
      </div>
    </div>
  </div>
)}

   </div>
 );
};


export default App;

 