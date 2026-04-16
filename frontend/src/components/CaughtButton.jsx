import { useState, useEffect } from "react";
import api from "../api";
import { useStore } from "../store";

const CATCH_RADIUS_M = 50; // must be within 50m of fugitive

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

export default function CaughtButton({ game, gameId }) {
  const user = useStore((s) => s.user);
  const [myPos, setMyPos] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!navigator.geolocation) return;
    const id = navigator.geolocation.watchPosition(
      (p) => setMyPos([p.coords.latitude, p.coords.longitude]),
      () => {},
      { enableHighAccuracy: true, maximumAge: 5000 }
    );
    return () => navigator.geolocation.clearWatch(id);
  }, []);

  if (game.status !== "hunting") return null;

  // Find fugitive position
  const players = game.players || {};
  const round = game.current_round || 0;
  const roundOrder = game.round_order || [];
  const fugitiveId = roundOrder[round]?.fugitive;
  const fugitive = fugitiveId ? players[fugitiveId] : null;

  let dist = null;
  let canCatch = false;
  if (myPos && fugitive?.lat) {
    dist = haversine(myPos[0], myPos[1], fugitive.lat, fugitive.lon);
    canCatch = dist <= CATCH_RADIUS_M;
  }

  const handleCaught = async () => {
    if (!canCatch) return;
    setLoading(true);
    try {
      await api.post(`/games/${gameId}/caught`);
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="caught-container">
      <button
        className={`caught-btn ${canCatch ? "active" : "disabled"}`}
        onClick={handleCaught}
        disabled={!canCatch || loading}
      >
        🎯 ¡Cazado!
      </button>
      {dist !== null && (
        <p className="catch-dist">
          {canCatch ? "✅ ¡Estás cerca! Pulsa para cazar" : `📍 ${Math.round(dist)}m del fugitivo (necesitas <${CATCH_RADIUS_M}m)`}
        </p>
      )}
      {!fugitive?.lat && <p className="catch-dist">Ubicación del fugitivo desconocida</p>}
    </div>
  );
}
