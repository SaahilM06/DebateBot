import React from 'react';
import AudioRecorder from './components /AudioRecorder';
import './App.css';
import Dropdown from "./components /Dropdown";
import { useState } from 'react';
import VoiceActivityDot from './components /VoiceActivityDot';


function App() {
  const [file, setFile] = useState<File | null>(null); 
  const [billFile, setBillFile] = useState<File | null>(null);

  const handleSideSelect = (side: string) => {
    console.log("User chose:", side);
    // Save this choice to state or context
  };
  
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleBillFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setBillFile(selectedFile);
    }
  };


  const handleSubmit = async () => {
    if(!file) {
      alert("make a choice before submitting");
      return;
    }

    const formData = new FormData();
    formData.append("file_upload", file);
    try {
      const response = await fetch("http://localhost:8000/file-choice/", {
          method: "POST", 
  
          body: formData
      });

      if(!response.ok){
          throw new Error("failed to submit");
      }

      const result = await response.json();
      alert(result.message);
      setFile(null)

  } catch(error){
      console.error("error ", error);
  }
  }


  const handleBillSubmit = async () => {
    if (!billFile) {
      alert("Upload your bill first.");
      return;
    }

    const formData = new FormData();
    formData.append("file_upload", billFile);
    try {
      const response = await fetch("http://localhost:8000/bill-choice/", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      alert(result.message);
      setBillFile(null);
    } catch (error) {
      console.error("Bill submit error", error);
    }
  };
  

  const handleVectorize = async () => {
    try {
      const response = await fetch("http://localhost:8000/run-vectorize/", {
        method: "POST",
      });
  
      const result = await response.json();
      if (result.message) {
        alert(result.message);
        console.log(result.output);  // optional: see terminal output
      } else {
        alert("Error: " + result.error);
      }
    } catch (error) {
      console.error("Vectorization error:", error);
    }
  };
  
  return (
    <div className="App">
      
      <h1>Debate Bot Recorder</h1>
    <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",  
      gap: "1rem",          
      marginTop: "2rem",
   }}
>
  <Dropdown
    options={["Affirmative", "Negative"]}
    onSelect={handleSideSelect}
    label="Choose Your Side"
  />


   <p>Submit your reference speech here</p>
  <input type="file" onChange={handleFileChange} />

  <button onClick={handleSubmit} style={{ marginTop: "1rem" }}>
        Submit Choice
    </button>
    


    <p>Submit your bill  here</p>
  <input type="file" onChange={handleBillFileChange} />

  <button onClick={handleBillSubmit} style={{ marginTop: "1rem" }}>
        Submit Choice
    </button>
  
    <button onClick={handleVectorize} style={{ marginTop: "1rem" }}>
        process
    </button>
  </div>


      <AudioRecorder />

      <VoiceActivityDot />

    </div>
  );
}

export default App;
