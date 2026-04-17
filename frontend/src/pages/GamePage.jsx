import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api";
import { useStore } from "../store";
import MapView from "../components/MapView";
import QuestionsView from "../components/QuestionsView";
import CardsView from "../components/CardsView";
import RankingView from "../components/RankingView";
import Timer from "../components/Timer";
import CaughtButton from "../components/CaughtButton";
import FugitiveNotification from "../components/FugitiveNotification";
import PendingQuestionPopup from "../components/PendingQuestionPopup";

export default function GamePage() {
  const { gameId } = useParams();
  const navigate = useNavigate();
  const { setGame, myRole, game, user } = useStore();
  const [tab, setTab] = useState("map");
  const [locationGranted, setLocationGranted] = useState(false);
  const [ending, setEnding] = useState(false);
  const [radarPreview, setRadarPreview] = useState(null);

  // Force to cards tab if hand exceeds 5
  useEffect(() => {
    if (!game || myRole !== "fugitive") return;
    const hand = game.players?.[String(user?.id)]?.hand || [];
    if (hand.length > 5) setTab("cards");
  }, [game?.players]);

  // Request geolocation permission immediately on mount
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      () => setLocationGranted(true),
      () => alert("⚠️ Activa la ubicación para jugar correctamente"),
      { enableHighAccuracy: true }
    );
  }, []);

  // Poll game state every 4s
  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get(`/games/${gameId}`);
        setGame(data);
        if (data.status === "finished") navigate("/lobby");
      } catch {}
    };
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, [gameId]);

  // Send location every 10s
  useEffect(() => {
    if (!navigator.geolocation) return;
    const send = (pos) => {
      api.post("/players/location", {
        game_id: gameId,
        lat: pos.coords.latitude,
        lon: pos.coords.longitude,
      }).catch(() => {});
    };
    const watchId = navigator.geolocation.watchPosition(send, () => {}, {
      enableHighAccuracy: true,
      maximumAge: 10000,
    });
    return () => navigator.geolocation.clearWatch(watchId);
  }, [gameId]);

  const endGame = useCallback(async () => {
    if (!confirm("¿Seguro que quieres acabar la partida?")) return;
    setEnding(true);
    try {
      await api.post(`/games/${gameId}/end`);
      navigate("/lobby");
    } catch (err) {
      alert(err.response?.data?.detail || "Error al acabar la partida");
      setEnding(false);
    }
  }, [gameId, navigate]);

  if (!game) return <div className="loading">Cargando partida...</div>;

  const hunterTabs = [
    { id: "map", label: "🗺️ Mapa" },
    { id: "questions", label: "❓ Preguntas" },
    { id: "ranking", label: "🏆 Ranking" },
  ];
  const fugitiveTabs = [
    { id: "map", label: "🗺️ Mapa" },
    { id: "cards", label: "🃏 Cartas" },
    { id: "ranking", label: "🏆 Ranking" },
  ];
  const tabs = myRole === "hunter" ? hunterTabs : fugitiveTabs;

  return (
    <div className="game-page">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 8px", background: "#1a1a2e" }}>
        <Timer game={game} role={myRole} />
      {myRole === "hunter" && <CaughtButton game={game} gameId={gameId} />}
      {myRole === "fugitive" && <FugitiveNotification game={game} gameId={gameId} />}
        <button
          onClick={endGame}
          disabled={ending}
          style={{
            background: "#e74c3c",
            color: "white",
            border: "none",
            borderRadius: 8,
            padding: "6px 14px",
            fontSize: 13,
            fontWeight: "bold",
            cursor: "pointer",
            opacity: ending ? 0.6 : 1,
          }}
        >
          🏁 Acabar
        </button>
      </div>

      <div className="tab-content">
        {tab === "map" && <MapView game={game} myRole={myRole} gameId={gameId} radarPreview={radarPreview} />}
        {tab === "questions" && myRole === "hunter" && <QuestionsView game={game} gameId={gameId} />}
        {tab === "cards" && myRole === "fugitive" && <CardsView game={game} gameId={gameId} />}
        {tab === "ranking" && <RankingView />}
      </div>

      {myRole === "fugitive" && (
        <PendingQuestionPopup
          game={game} gameId={gameId} myRole={myRole}
          onShowRadarPreview={(pending) => {
            setRadarPreview(pending);
            setTab("map");
          }} />
      )}

      <nav className="bottom-nav">
        {tabs.map((t) => (
          <button key={t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
