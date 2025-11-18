import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/navbar';
import Landing from './pages/landing';
import StartInterview from './pages/startinterview';


function App(){
return (
<div>
<Navbar />
<main style={{ padding: '1rem' }}>
<Routes>
<Route path="/" element={<Landing />} />
<Route path="/start" element={<StartInterview />} />
</Routes>
</main>
</div>
);
}


export default App;