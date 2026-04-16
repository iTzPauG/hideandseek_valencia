import { useState, useEffect } from "react";
import api from "../api";
import { useStore } from "../store";

const REWARD_LABELS = {
  "time_10": "+10 min ⏱", "time_20": "+20 min ⏱", "time_30": "+30 min ⏱", "time_60": "+1h ⏱",
  "veto": "Veto 🚫", "randomize": "Randomizar 🔀", "expand_hideout": "Ampliar escondite 📍",
  "change_hideout": "Cambiar escondite 🚇", "freeze": "Congelar 🧊", "duplicate": "Duplicar ✌️",
};

function cardLabel(id) {
  const prefix = id.replace(/_\d+$/, "");
  return REWARD_LABELS[prefix] || id;
}

export default function FugitiveNotification({ game, gameId }) {
  const user = useStore((s) => s.user);
  const [phase, setPhase] = useState("question"); // "question" | "reward"
  const [drawnCards, setDrawnCards] = useState([]);
  const [chosen, setChosen] = useState([]);
  const [allCards, setAllCards] = useState([]);
  const [loading, setLoading] = useState(false);

  const pending = game.pending_question;
  const player = game.players?.[String(user?.id)] || {};
  const hand = player.hand || [];

  const hasVeto = hand.some(c => c.startsWith("veto_"));
  const hasRandomize = hand.some(c => c.startsWith("randomize_"));

  useEffect(() => {
    if (pending?.status === "pending") {
      setPhase("question");
      setChosen([]);
    }
    if (pending?.status === "answered") {
      // Draw cards for reward
      api.get("/map/stations").catch(() => {}); // keep alive
      api.get("/questions/list").then(({ data: qs }) => {
        // Draw from cards collection
        api.get("/cards/list").then(({ data: cards }) => {
          setAllCards(cards);
          const reward = pending.reward || { draw: 2, keep: 1 };
          // Shuffle and draw
          const shuffled = [...cards].sort(() => Math.random() - 0.5);
          setDrawnCards(shuffled.slice(0, reward.draw));
          setPhase("reward");
        }).catch(() => {});
      }).catch(() => {});
    }
  }, [pending?.status, pending?.question_id]);

  if (!pending || pending.status === "vetoed" || pending.status === null) return null;
  if (phase === "question" && pending.status !== "pending") return null;
  if (phase === "reward" && pending.status !== "answered") return null;

  const respond = async (action, answer = null) => {
    setLoading(true);
    try {
      await api.post("/questions/respond", { game_id: gameId, action, answer });
      if (action !== "veto") setPhase("reward");
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    } finally {
      setLoading(false);
    }
  };

  const claimReward = async () => {
    const keep = pending.reward?.keep || 1;
    if (chosen.length !== keep) {
      alert(`Debes elegir exactamente ${keep} carta${keep > 1 ? "s" : ""}`);
      return;
    }
    setLoading(true);
    try {
      await api.post("/questions/claim-reward", { game_id: gameId, chosen_card_ids: chosen });
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    } finally {
      setLoading(false);
    }
  };

  const toggleChosen = (id) => {
    const keep = pending.reward?.keep || 1;
    if (chosen.includes(id)) {
      setChosen(chosen.filter(c => c !== id));
    } else if (chosen.length < keep) {
      setChosen([...chosen, id]);
    }
  };

  return (
    <div className="fugitive-notification-overlay">
      <div className="fugitive-notification-box">
        {phase === "question" && (
          <>
            <p className="notif-label">📨 El cazador pregunta:</p>
            <h3>{pending.title}</h3>
            <p className="notif-desc">{pending.description}</p>

            <div className="notif-actions">
              {pending.category === "match" && (
                <>
                  <button className="notif-btn yes" onClick={() => respond("answer", true)} disabled={loading}>✅ Sí</button>
                  <button className="notif-btn no" onClick={() => respond("answer", false)} disabled={loading}>❌ No</button>
                </>
              )}
              {pending.category === "photo" && (
                <button className="notif-btn yes" onClick={() => respond("answer", true)} disabled={loading}>📸 Foto enviada por WhatsApp</button>
              )}
              <button
                className={`notif-btn veto ${!hasVeto ? "disabled-card" : ""}`}
                onClick={() => hasVeto && respond("veto")}
                disabled={loading || !hasVeto}
                title={!hasVeto ? "Necesitas carta de Veto" : ""}
              >🚫 Vetar {!hasVeto && <span className="no-card">sin carta</span>}</button>
              <button
                className={`notif-btn rand ${!hasRandomize ? "disabled-card" : ""}`}
                onClick={() => hasRandomize && respond("randomize")}
                disabled={loading || !hasRandomize}
                title={!hasRandomize ? "Necesitas carta de Randomizar" : ""}
              >🔀 Randomizar {!hasRandomize && <span className="no-card">sin carta</span>}</button>
            </div>
          </>
        )}

        {phase === "reward" && (
          <>
            <p className="notif-label">🎁 Elige {pending.reward?.keep || 1} carta{(pending.reward?.keep || 1) > 1 ? "s" : ""} de recompensa</p>
            <p className="notif-subdesc">Has robado {drawnCards.length} cartas, quédate {pending.reward?.keep || 1}</p>
            <div className="reward-cards">
              {drawnCards.map(card => (
                <div
                  key={card.id}
                  className={`reward-card ${chosen.includes(card.id) ? "chosen" : ""}`}
                  onClick={() => toggleChosen(card.id)}
                >
                  <span>{cardLabel(card.id)}</span>
                </div>
              ))}
            </div>
            <button className="notif-btn yes" onClick={claimReward} disabled={loading || chosen.length !== (pending.reward?.keep || 1)}>
              Guardar cartas elegidas
            </button>
          </>
        )}
      </div>
    </div>
  );
}
