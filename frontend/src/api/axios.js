import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL + '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token'); // or useContext(AuthContext)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api
