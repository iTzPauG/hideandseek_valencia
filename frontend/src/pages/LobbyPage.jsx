import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { useStore } from "../store";

const STATUS_LABEL = {
  waiting: "Esperando", hiding: "Escondiéndose",
  hunting: "Cazando", changing_hideout: "Cambiando escondite",
};

export default function LobbyPage() {
  const [code, setCode] = useState("");
  const [rounds, setRounds] = useState(3);
  const [gameCode, setGameCode] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [joined, setJoined] = useState(false);
  const [playerCount, setPlayerCount] = useState(1);
  const [activeGames, setActiveGames] = useState([]);
  const [error, setError] = useState("");
  const user = useStore((s) => s.user);
  const logout = useStore((s) => s.logout);
  const navigate = useNavigate();
  const pollRef = useRef(null);

  useEffect(() => {
    api.get("/games/active/mine").then(({ data }) => setActiveGames(data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!gameId) return;
    const poll = async () => {
      try {
        const { data } = await api.get(`/games/${gameId}`);
        setPlayerCount(Object.keys(data.players || {}).length);
        if (data.status !== "waiting") {
          clearInterval(pollRef.current);
          navigate(`/game/${gameId}`);
        }
      } catch (_) {}
    };
    pollRef.current = setInterval(poll, 3000);
    return () => clearInterval(pollRef.current);
  }, [gameId, navigate]);

  const createGame = async () => {
    try {
      const { data } = await api.post("/games/create", { rounds });
      setGameCode(data.code);
      setGameId(data.game_id);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al crear partida");
    }
  };

  const joinGame = async () => {
    try {
      const { data } = await api.post("/games/join", { code: code.toUpperCase() });
      setGameId(data.game_id);
      setJoined(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Código inválido");
    }
  };

  const startGame = async () => {
    try {
      await api.post(`/games/${gameId}/start`);
      navigate(`/game/${gameId}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al iniciar");
    }
  };

  return (
    <div className="lobby-page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Hola, {user?.username} 👋</h2>
        <button onClick={() => { logout(); navigate("/"); }} style={{ padding: "8px 16px" }}>Cerrar sesión</button>
      </div>
      {error && <p className="error">{error}</p>}

      {!gameCode && !joined && (
        <>
          {activeGames.length > 0 && (
            <section className="active-games">
              <h3>🔄 Partidas en progreso</h3>
              {activeGames.map((g) => (
                <button key={g.game_id} className="active-game-btn" onClick={() => navigate(`/game/${g.game_id}`)}>
                  <span>Código: <strong>{g.code}</strong></span>
                  <span className="status-badge">{STATUS_LABEL[g.status] || g.status}</span>
                </button>
              ))}
            </section>
          )}
          <section>
            <h3>Crear partida</h3>
            <label>Rondas: <input type="number" min={1} max={10} value={rounds} onChange={(e) => setRounds(+e.target.value)} /></label>
            <button onClick={createGame}>Crear</button>
          </section>
          <hr />
          <section>
            <h3>Unirse a partida</h3>
            <input placeholder="Código (6 caracteres)" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} maxLength={6} />
            <button onClick={joinGame}>Unirse</button>
          </section>
          <hr />
          <button onClick={() => navigate("/ranking")}>🏆 Ranking</button>
        </>
      )}

      {gameCode && (
        <div className="waiting-room">
          <h3>Partida creada</h3>
          <p>Comparte este código con tu rival:</p>
          <div className="game-code">{gameCode}</div>
          <p className="player-count">Jugadores: {playerCount}/2</p>
          {playerCount >= 2
            ? <button onClick={startGame}>▶ Empezar partida</button>
            : <p>Esperando al segundo jugador...</p>
          }
        </div>
      )}

      {joined && !gameCode && (
        <div className="waiting-room">
          <h3>Te has unido a la partida ✅</h3>
          <p>Esperando a que el creador inicie el juego...</p>
          <div className="pulse-dot" />
        </div>
      )}
    </div>
  );
}
