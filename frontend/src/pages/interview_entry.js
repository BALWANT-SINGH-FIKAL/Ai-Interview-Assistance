import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function InterviewEntry() {
    const navigate = useNavigate();

    const [resumeText, setResumeText] = useState("");
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [suggestedCategories, setSuggestedCategories] = useState([]);

    // ---------------------------------
    //     Resume Upload Handler
    // ---------------------------------
    const handleResumeUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            setResumeText(text);

            autoSuggestCategories(text);
        };

        reader.readAsText(file);
    };

    // ---------------------------------
    //  Fake AI Resume Parsing
    // ---------------------------------
    const autoSuggestCategories = (text) => {
        const skillsFound = [];

        const techKeywords = ["python", "java", "react", "sql", "ml", "ai"];
        const hrKeywords = ["team", "leadership", "communication"];
        const behaviorKeywords = ["challenge", "project", "problem solving"];

        techKeywords.forEach((t) => {
            if (text.toLowerCase().includes(t)) skillsFound.push("technical");
        });

        hrKeywords.forEach((t) => {
            if (text.toLowerCase().includes(t)) skillsFound.push("hr");
        });

        behaviorKeywords.forEach((t) => {
            if (text.toLowerCase().includes(t))
                skillsFound.push("behavioral");
        });

        const unique = [...new Set(skillsFound)];
        unique.push("resume_based");

        setSuggestedCategories(unique.length ? unique : ["resume_based"]);
    };

    // ---------------------------------
    //  Start Interview (navigate)
    // ---------------------------------
    const startInterview = () => {
        if (!selectedCategory) {
            alert("Please select an interview type");
            return;
        }

        navigate("/interview", { state: { selectedCategory } });
    };

    return (
        <div style={{ padding: 20, maxWidth: 700, margin: "0 auto" }}>
            <h2>Start Your AI Interview</h2>
            <p>Upload resume → select interview type → start interview</p>

            {/* Resume Upload */}
            <div style={{ marginTop: 20 }}>
                <input
                    type="file"
                    accept=".txt,.md,.pdf"
                    onChange={handleResumeUpload}
                />
            </div>

            {/* Suggested Categories */}
            {suggestedCategories.length > 0 && (
                <div style={{ marginTop: 20 }}>
                    <h3>Suggested Interview Types</h3>

                    {suggestedCategories.map((cat) => (
                        <button
                            key={cat}
                            style={{
                                margin: 5,
                                padding: "10px 18px",
                                borderRadius: 8,
                                background:
                                    selectedCategory === cat ? "#222" : "#eee",
                                color:
                                    selectedCategory === cat ? "#fff" : "#000",
                            }}
                            onClick={() => setSelectedCategory(cat)}
                        >
                            {cat.toUpperCase()}
                        </button>
                    ))}
                </div>
            )}

            {/* Start Interview Button */}
            <div style={{ marginTop: 30 }}>
                <button
                    style={{
                        padding: "12px 20px",
                        background: "#000",
                        color: "#fff",
                        borderRadius: 8,
                    }}
                    onClick={startInterview}
                >
                    Start Interview
                </button>
            </div>
        </div>
    );
}
