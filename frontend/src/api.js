import axios from 'axios';


const base = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
export const ping = () => axios.get(`${base}/ping`);