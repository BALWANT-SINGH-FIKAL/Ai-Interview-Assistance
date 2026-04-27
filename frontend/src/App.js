import React from "react";
import { Routes, Route } from "react-router-dom";

import Navbar from "./components/navbar";
import Landing from "./pages/landing";
import InterviewEntry from "./pages/interview_entry";   // resume upload page
import Interview from "./components/interview";         // main interview page

function App() {
  return (
    <div>
      <Navbar />

      <main style={{ padding: "1rem" }}>
        <Routes>
          {/* Homepage */}
          <Route path="/" element={<Landing />} />

          {/* Resume upload + category selection */}
          <Route path="/start" element={<InterviewEntry />} />

          {/* Actual interview */}
          <Route path="/interview" element={<Interview />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
