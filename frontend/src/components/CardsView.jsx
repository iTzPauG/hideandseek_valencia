import { useState } from "react";
import api from "../api";
import { useStore } from "../store";

const CARD_ICONS = {
  time: "⏱", expand_hideout: "📍", change_hideout: "🚇",
  freeze_hunters: "🧊", veto: "🚫", randomize: "🔀", duplicate: "✌️",
  challenge: "🎯",
};

export default function CardsView({ game, gameId }) {
  const user = useStore((s) => s.user);
  const [selected, setSelected] = useState(null);
  const [rewards, setRewards] = useState(null);

  const player = game.players?.[String(user?.id)] || {};
  const hand = player.hand || [];

  const playCard = async (cardId) => {
    try {
      await api.post("/cards/play", { game_id: gameId, card_id: cardId });
      setSelected(null);
    } catch (err) {
      alert(err.response?.data?.detail || "Error al jugar carta");
    }
  };

  return (
    <div className="cards-view">
      <div className="cards-header">
        <h3>Mis cartas ({hand.length}/5)</h3>
        {rewards && (
          <button className="rewards-btn" onClick={() => setRewards(null)}>
            🎁 Recompensas
          </button>
        )}
      </div>

      <div className="cards-grid">
        {hand.map((cardId) => (
          <div
            key={cardId}
            className={`card ${selected === cardId ? "selected" : ""}`}
            onClick={() => setSelected(selected === cardId ? null : cardId)}
          >
            <span className="card-icon">{CARD_ICONS[cardId.split("_")[0]] || "🃏"}</span>
            <span className="card-name">{cardId}</span>
          </div>
        ))}
        {hand.length === 0 && <p className="empty">No tienes cartas en mano</p>}
      </div>

      {selected && (
        <div className="card-actions">
          <button onClick={() => playCard(selected)}>▶ Usar carta</button>
          <button onClick={() => setSelected(null)}>Cancelar</button>
        </div>
      )}
    </div>
  );
}
