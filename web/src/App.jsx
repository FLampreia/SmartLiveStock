import { useEffect, useState } from 'react';

function App() {
  const [sheepCount, setSheepCount] = useState(0);
  const [jetsonStatus, setJetsonStatus] = useState("Desconhecido");
  const API_URL = import.meta.env.VITE_API_URL; // lê do .env

  console.log("API_URL:", API_URL);

  // 🔁 Atualiza a contagem a cada 2 segundos
  useEffect(() => {
    async function fetchCount() {
      try {
        const response = await fetch(`${API_URL}/api/count`);
        const data = await response.json();
        setSheepCount(data.sheep_count);
      } catch (err) {
        console.error("Erro ao buscar contagem:", err);
      }
    }

    fetchCount();
    const interval = setInterval(fetchCount, 2000);
    return () => clearInterval(interval);
  }, [API_URL]);

  // 🚀 Funções para enviar comandos Start/Stop ao servidor central
async function handleCommand(action) {
  try {
    const response = await fetch(`${API_URL}/jetson/command?action=${action}`);
    const data = await response.json();
    if (response.ok) {
      setJetsonStatus(data.status || `Comando '${action}' enviado`);
    } else {
      setJetsonStatus(`Erro: ${data.detail || "Falha ao enviar comando"}`);
    }
  } catch (err) {
    console.error("Erro ao enviar comando:", err);
    setJetsonStatus("Erro de comunicação com o servidor");
  }
}


  return (
    <div style={{ textAlign: "center", marginTop: "40px", fontFamily: "sans-serif" }}>
      <h1>🐑 Ovelhas Contadas: {sheepCount}</h1>

      <div style={{ marginTop: "30px" }}>
        <button
          onClick={() => handleCommand("start")}
          style={{ marginRight: "15px", padding: "10px 20px", cursor: "pointer" }}
        >
          ▶️ Iniciar Jetson
        </button>

        <button
          onClick={() => handleCommand("stop")}
          style={{ padding: "10px 20px", cursor: "pointer" }}
        >
          ⏹️ Parar Jetson
        </button>
      </div>

      <h2 style={{ marginTop: "40px", color: "#555" }}>
        Estado atual da Jetson: <span style={{ color: "#0066cc" }}>{jetsonStatus}</span>
      </h2>
    </div>
  );
}

export default App;
