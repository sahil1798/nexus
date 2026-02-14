import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  headers: { 'Content-Type': 'application/json' },
});

export const getStatus = () => api.get('/status');
export const getServers = () => api.get('/servers');
export const registerServer = (data) => api.post('/servers/register', data);
export const deleteServer = (name) => api.delete(`/servers/${name}`);
export const getGraph = () => api.get('/graph');
export const rebuildGraph = () => api.post('/graph/rebuild');
export const discoverPipeline = (data) => api.post('/discover', data);
export const executePipeline = (data) => api.post('/execute', data);
export const getHistory = () => api.get('/history');

export default api;
