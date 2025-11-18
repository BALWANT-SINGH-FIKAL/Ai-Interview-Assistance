import React from 'react';
import { Link } from 'react-router-dom';


export default function Navbar(){
return (
<nav>
<div className="container" style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
<div>
<Link to="/">AI Interview Assistant</Link>
</div>
<div>
<Link to="/">Home</Link>
<Link to="/start">Start</Link>
</div>
</div>
</nav>
);
}