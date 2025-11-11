import { useState } from "react";

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const testCORS = async () => {
    try {
      const response = await fetch("http://192.168.1.66:8070/");
      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }
      const json = await response.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err.message);
      setData(null);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>Teste de CORS com FastAPI</h1>
      <button onClick={testCORS}>Testar ligação</button>

      {data && (
        <p style={{ color: "green" }}>
          Sucesso! Resposta: {JSON.stringify(data)}
        </p>
      )}
      {error && (
        <p style={{ color: "red" }}>
          Falha na requisição: {error}
        </p>
      )}
    </div>
  );
}

export default App;
