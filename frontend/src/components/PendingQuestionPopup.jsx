import { useState } from "react";
import api from "../api";
import { useStore } from "../store";

const CARD_ICONS = {
  time: "⏱", expand_hideout: "📍", change_hideout: "🚇",
  freeze_hunters: "🧊", veto: "🚫", randomize: "🔀", duplicate: "✌️", challenge: "🎯",
};

export default function PendingQuestionPopup({ game, gameId, myRole, onShowRadarPreview }) {
  const user = useStore((s) => s.user);
  const pending = game.pending_question;
  const [phase, setPhase] = useState("main"); // main | reward
  const [drawnCards, setDrawnCards] = useState([]);
  const [selectedCards, setSelectedCards] = useState([]);
  const [loading, setLoading] = useState(false);

  if (!pending || pending.status !== "pending") return null;
  if (myRole !== "fugitive") return null;

  const player = game.players?.[String(user?.id)] || {};
  const hand = player.hand || [];
  const hasVeto = hand.some(c => c.startsWith("veto_"));
  const hasRandomize = hand.some(c => c.startsWith("randomize_"));
  const reward = pending.reward || { draw: 2, keep: 1 };

  const respond = async (action, extra = {}) => {
    setLoading(true);
    try {
      const { data } = await api.post("/questions/respond", { game_id: gameId, action, ...extra });
      if (action === "answer" || action === "radar_accept") {
        // Draw cards for reward
        const cards = await api.get(`/cards/draw?count=${reward.draw}`);
        setDrawnCards(cards.data || []);
        setPhase("reward");
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    } finally {
      setLoading(false);
    }
  };

  const toggleCard = (cardId) => {
    setSelectedCards(prev =>
      prev.includes(cardId) ? prev.filter(c => c !== cardId) : [...prev, cardId]
    );
  };

  const claimReward = async () => {
    if (selectedCards.length > reward.keep) {
      alert(`Solo puedes quedarte ${reward.keep} carta${reward.keep > 1 ? "s" : ""}`);
      return;
    }
    setLoading(true);
    try {
      await api.post("/questions/claim-reward", { game_id: gameId, chosen_card_ids: selectedCards });
      const newTotal = hand.length + selectedCards.length;
      if (newTotal > 5) {
        // Force discard — redirect handled by GamePage watching hand.length > 5
      }
      setPhase("main");
      setDrawnCards([]);
      setSelectedCards([]);
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pq-overlay">
      <div className="pq-box">
        {phase === "main" && <>
          <div className="pq-header">
            <span className="pq-cat">📡 {pending.category === "radar" ? "Radar" : pending.category}</span>
            <strong>{pending.title}</strong>
            <p className="pq-desc">{pending.description}</p>
          </div>
          <div className="pq-btns">
            <button className="pq-btn primary" disabled={loading}
              onClick={() => respond("answer")}>
              ✅ Responder
            </button>
            <button className="pq-btn" disabled={loading}
              onClick={() => onShowRadarPreview && onShowRadarPreview(pending)}>
              👁 Mostrar efecto
            </button>
            <button className={`pq-btn ${!hasVeto ? "disabled" : ""}`}
              disabled={loading || !hasVeto}
              onClick={() => hasVeto && respond("veto")}>
              🚫 Vetar
            </button>
            <button className={`pq-btn ${!hasRandomize ? "disabled" : ""}`}
              disabled={loading || !hasRandomize}
              onClick={() => hasRandomize && respond("randomize")}>
              🔀 Randomizar
            </button>
          </div>
        </>}

        {phase === "reward" && <>
          <strong>🎁 Elige {reward.keep} carta{reward.keep > 1 ? "s" : ""} (de {reward.draw})</strong>
          <div className="reward-cards">
            {drawnCards.map(card => (
              <div key={card.id}
                className={`reward-card ${selectedCards.includes(card.id) ? "selected" : ""}`}
                onClick={() => toggleCard(card.id)}>
                <span>{CARD_ICONS[card.type] || "🃏"}</span>
                <span>{card.name || card.id}</span>
                <div className="reward-check">{selectedCards.includes(card.id) ? "✓" : ""}</div>
              </div>
            ))}
          </div>
          <button className="pq-btn primary" disabled={loading || selectedCards.length !== reward.keep}
            onClick={claimReward}>
            Aceptar ({selectedCards.length}/{reward.keep})
          </button>
        </>}
      </div>
    </div>
  );
}
