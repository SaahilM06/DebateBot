import React, { useState } from "react";

interface DropdownProps {
  options: string[];
  onSelect: (value: string) => void;
  placeholder?: string;
  label?: string;
}

const Dropdown: React.FC<DropdownProps> = ({ options, onSelect, placeholder = "Select...", label }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (option: string) => {
    setSelected(option);
    onSelect(option);
    setIsOpen(false);
  };

  const handleSubmit = async () => {
    if(!selected) {
        alert("make a choice before submitting");
        return;
    }
    const filename = `submission.txt`;
    try {
        const response = await fetch("http://localhost:8000/submit-choice/", {
            method: "POST", 
            headers: {
                "Content-Type": "application/json",
              },
            body: JSON.stringify({ choice: selected }),
        });

        if(!response.ok){
            throw new Error("failed to submit");
        }

        const result = await response.json();
        alert(result.message);
        setSelected(null)

    } catch(error){
        console.error("error ", error);
    }
  }

  return (
    
    <div style={{ width: 200, position: "relative" }}>
      {label && <label>{label}</label>}
      <div
        style={{
          border: "1px solid gray",
          padding: "8px",
          gap: "1rem",
          background: "#fff",
          cursor: "pointer",
          userSelect: "none",
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        {selected || placeholder}
      </div>

      {isOpen && (
        <ul
          style={{
            position: "absolute",
            top: "75%",
            left: 0,
            right: 0,
            background: "#fff",
            border: "1px solid gray",
            borderTop: "none",
            zIndex: 10,
            margin: 0,
            padding: 0,
            listStyle: "none",
          }}
        >
          {options.map(option => (
            <li
              key={option}
              onClick={() => handleSelect(option)}
              style={{
                padding: "8px",
                cursor: "pointer",
              }}
            >
              {option}
            </li>
          ))}
        </ul>
      )}

    <button onClick={handleSubmit} style={{ marginTop: "1rem" }}>
        Submit Choice
    </button>
</div>
  );
};

export default Dropdown;
