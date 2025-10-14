// web/src/App.jsx
import { useEffect, useState } from 'react';

function App() {
  const [sheepCount, setSheepCount] = useState(0);
  const API_URL = import.meta.env.VITE_API_URL; // lê do .env

  useEffect(() => {
    async function fetchCount() {
      try {
        const response = await fetch(`${API_URL}/api/count`);
        const data = await response.json();
        setSheepCount(data.sheep_count);
      } catch (err) {
        console.error(err);
      }
    }

    fetchCount();
    const interval = setInterval(fetchCount, 2000);
    return () => clearInterval(interval);
  }, []);

  return <h1>Ovelhas Contadas: {sheepCount}</h1>;
}

export default App;
