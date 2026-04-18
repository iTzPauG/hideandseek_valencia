import { useEffect, useState, useCallback, useRef } from "react";
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

export default function GamePage() {
  const { gameId } = useParams();
  const navigate = useNavigate();
  const { setGame, myRole, game, user } = useStore();
  const [tab, setTab] = useState("map");
  const [ending, setEnding] = useState(false);
  const [radarPreview, setRadarPreview] = useState(null);
  const [stadiumPreview, setStadiumPreview] = useState(null);
  const [exploringMap, setExploringMap] = useState(false);

  useEffect(() => {
    if (!game || myRole !== "fugitive") return;
    const hand = game.players?.[String(user?.id)]?.hand || [];
    if (hand.length > 5) setTab("cards");
  }, [game?.players]);

  // Auto-switch to map after fugitive claims reward (pending_question cleared)
  const prevPendingRef = useRef(null);
  useEffect(() => {
    if (myRole !== "fugitive") return;
    const prev = prevPendingRef.current;
    const curr = game?.pending_question;
    if (prev && !curr) setTab("map"); // was pending, now null → reward claimed
    prevPendingRef.current = curr;
  }, [game?.pending_question]);

  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      () => {},
      () => alert("⚠️ Activa la ubicación para jugar correctamente"),
      { enableHighAccuracy: true }
    );
  }, []);

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

  useEffect(() => {
    if (!navigator.geolocation) return;
    const watchId = navigator.geolocation.watchPosition(
      (pos) => api.post("/players/location", { game_id: gameId, lat: pos.coords.latitude, lon: pos.coords.longitude }).catch(() => {}),
      () => {},
      { enableHighAccuracy: true, maximumAge: 10000 }
    );
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
        {myRole === "fugitive" && !exploringMap && (
          <FugitiveNotification game={game} gameId={gameId}
            onShowRadarPreview={(pending) => {
              if (pending.previewType === 'stadium') {
                setStadiumPreview(pending);
                setRadarPreview(null);
              } else {
                setRadarPreview(pending);
                setStadiumPreview(null);
              }
              setExploringMap(true);
              setTab("map");
            }} />
        )}
        <button onClick={endGame} disabled={ending}
          style={{ background: "#e74c3c", color: "white", border: "none", borderRadius: 8, padding: "6px 14px", fontSize: 13, fontWeight: "bold", cursor: "pointer", opacity: ending ? 0.6 : 1 }}>
          🏁 Acabar
        </button>
      </div>

      <div className="tab-content">
        {tab === "map" && <MapView game={game} myRole={myRole} gameId={gameId} radarPreview={radarPreview} stadiumPreview={stadiumPreview} />}
        {!exploringMap && tab === "questions" && myRole === "hunter" && (
          <QuestionsView game={game} gameId={gameId}
            onShowMap={() => setTab("map")}
            onPreviewRadar={(p) => { setRadarPreview(p); setExploringMap(true); setTab("map"); }}
            onPreviewStadiums={(s) => {
              setStadiumPreview(s);
              setExploringMap(true);
              setTab("map");
            }} />
        )}
        {!exploringMap && tab === "cards" && myRole === "fugitive" && <CardsView game={game} gameId={gameId} />}
        {!exploringMap && tab === "ranking" && <RankingView game={game} />}
      </div>

      {exploringMap ? (
        <>
          {stadiumPreview && !Array.isArray(stadiumPreview) && (stadiumPreview.hunter_stadium || stadiumPreview.previewType === 'turia') && (
            <div style={{ background: stadiumPreview.is_hit ? '#1a3a1a' : '#3a1a1a', padding: '0.4rem 1rem', textAlign: 'center', fontSize: '0.9rem', borderTop: `2px solid ${stadiumPreview.is_hit ? '#00e676' : '#e74c3c'}` }}>
              {stadiumPreview.previewType === 'turia'
                ? (stadiumPreview.is_hit ? '🎯 IT\'S A HIT — Más cerca del Turia' : '💨 IT\'S A MISS — Más lejos del Turia')
                : (stadiumPreview.is_hit ? '🎯 IT\'S A HIT — Estadio: ' : '💨 IT\'S A MISS — Estadio: ')
              }
              {stadiumPreview.hunter_stadium && <strong>{stadiumPreview.hunter_stadium}</strong>}
            </div>
          )}
          <button className="explore-back-btn"
            onClick={() => { setExploringMap(false); setRadarPreview(null); setStadiumPreview(null); setTab(myRole === "hunter" ? "questions" : "map"); }}>
            ← Volver
          </button>
        </>
      ) : (
        <nav className="bottom-nav">
          {tabs.map((t) => (
            <button key={t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>
      )}
    </div>
  );
}
