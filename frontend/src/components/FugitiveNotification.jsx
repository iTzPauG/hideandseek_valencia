import { useState, useEffect } from "react";
import api from "../api";
import { useStore } from "../store";
import { STADIUM_GROUPS, TURIA_DISTS } from "../gameData.js";

const REWARD_LABELS = {
  "time_10": "+10 min ⏱", "time_20": "+20 min ⏱", "time_30": "+30 min ⏱", "time_60": "+1h ⏱",
  "veto": "Veto 🚫", "randomize": "Randomizar 🔀", "expand_hideout": "Ampliar escondite 📍",
  "change_hideout": "Cambiar escondite 🚇", "freeze": "Congelar 🧊", "duplicate": "Duplicar ✌️",
};

function cardLabel(id) {
  const prefix = id.replace(/_\d+$/, "");
  return REWARD_LABELS[prefix] || id;
}

export default function FugitiveNotification({ game, gameId, onShowRadarPreview }) {
  const user = useStore((s) => s.user);
  const [phase, setPhase] = useState("question");
  const [drawnCards, setDrawnCards] = useState([]);
  const [chosen, setChosen] = useState([]);
  const [loading, setLoading] = useState(false);

  const pending = game.pending_question;
  const player = game.players?.[String(user?.id)] || {};
  const hand = player.hand || [];
  const hasVeto = hand.some(c => c.startsWith("veto_"));
  const hasRandomize = hand.some(c => c.startsWith("randomize_"));

  useEffect(() => {
    if (pending?.status === "pending") { setPhase("question"); setChosen([]); }
    if (pending?.status === "answered") {
      api.get("/cards/list").then(({ data: cards }) => {
        const reward = pending.reward || { draw: 2, keep: 1 };
        const shuffled = [...cards].sort(() => Math.random() - 0.5);
        setDrawnCards(shuffled.slice(0, reward.draw));
        setPhase("reward");
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
    if (chosen.length !== keep) { alert(`Debes elegir exactamente ${keep} carta${keep > 1 ? "s" : ""}`); return; }
    setLoading(true);
    try {
      await api.post("/questions/claim-reward", { game_id: gameId, chosen_card_ids: chosen });
    } catch (err) {
      alert(err.response?.data?.detail || "Error al guardar cartas");
    } finally {
      setLoading(false);
    }
  };

  const toggleChosen = (id) => {
    const keep = pending.reward?.keep || 1;
    if (chosen.includes(id)) setChosen(chosen.filter(c => c !== id));
    else if (chosen.length < keep) setChosen([...chosen, id]);
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
              {pending.category === "radar" && (
                <>
                  <button className="notif-btn yes" onClick={() => respond("answer")} disabled={loading}>✅ Responder</button>
                  <button className="notif-btn" onClick={() => onShowRadarPreview && onShowRadarPreview(pending)} disabled={loading}>👁 Mostrar efecto</button>
                </>
              )}
              {pending.question_id === "match_turia" && (
                <>
                  <p style={{color:'#aaa',fontSize:'0.85rem',marginBottom:'0.5rem'}}>
                    🌊 Cazador a <strong style={{color:'#fff'}}>{Math.round(pending.hunter_turia_dist)}m</strong> del Turia
                  </p>
                  <button className="notif-btn yes" onClick={() => respond("answer")} disabled={loading}>✅ Responder</button>
                  <button className="notif-btn" onClick={() => {
                    const fd = TURIA_DISTS[game.fugitive_station] || 99999;
                    const hit = fd <= pending.hunter_turia_dist;
                    onShowRadarPreview && onShowRadarPreview({...pending, previewType:'turia', is_hit: hit, hunter_dist: pending.hunter_turia_dist});
                  }} disabled={loading}>👁 Mostrar efecto</button>
                </>
              )}
              {pending.question_id === "match_stadium" && (
                <>
                  <p style={{color:'#aaa',fontSize:'0.85rem',marginBottom:'0.5rem'}}>
                    🏟 Estadio del cazador: <strong style={{color:'#fff'}}>{pending.hunter_stadium}</strong>
                  </p>
                  <button className="notif-btn yes" onClick={() => respond("answer")} disabled={loading}>✅ Responder</button>
                  <button className="notif-btn" onClick={() => {
                    const fs = game.fugitive_station;
                    const fStadium = Object.entries(STADIUM_GROUPS).find(([,s]) => s.includes(fs))?.[0];
                    const hit = fStadium === pending.hunter_stadium;
                    onShowRadarPreview && onShowRadarPreview({...pending, previewType:'stadium', is_hit: hit});
                  }} disabled={loading}>👁 Mostrar efecto</button>
                </>
              )}
              {pending.category === "match" && !["match_stadium","match_turia"].includes(pending.question_id) && (
                <>
                  <button className="notif-btn yes" onClick={() => respond("answer", true)} disabled={loading}>✅ Sí</button>
                  <button className="notif-btn no" onClick={() => respond("answer", false)} disabled={loading}>❌ No</button>
                </>
              )}
              {pending.category === "photo" && (
                <button className="notif-btn yes" onClick={() => respond("answer", true)} disabled={loading}>📸 Foto enviada por WhatsApp</button>
              )}
              <button className={`notif-btn veto ${!hasVeto ? "disabled-card" : ""}`}
                onClick={() => hasVeto && respond("veto")} disabled={loading || !hasVeto}>
                🚫 Vetar {!hasVeto && <span className="no-card">sin carta</span>}
              </button>
              <button className={`notif-btn rand ${!hasRandomize ? "disabled-card" : ""}`}
                onClick={() => hasRandomize && respond("randomize")} disabled={loading || !hasRandomize}>
                🔀 Randomizar {!hasRandomize && <span className="no-card">sin carta</span>}
              </button>
            </div>
          </>
        )}
        {phase === "reward" && (
          <>
            <p className="notif-label">🎁 Elige {pending.reward?.keep || 1} carta{(pending.reward?.keep || 1) > 1 ? "s" : ""} de recompensa</p>
            <p className="notif-subdesc">Has robado {drawnCards.length} cartas, quédate {pending.reward?.keep || 1}</p>
            <div className="reward-cards">
              {drawnCards.map(card => (
                <div key={card.id} className={`reward-card ${chosen.includes(card.id) ? "chosen" : ""}`}
                  onClick={() => toggleChosen(card.id)}>
                  <span>{cardLabel(card.id)}</span>
                </div>
              ))}
            </div>
            <button className="notif-btn yes" onClick={claimReward}
              disabled={loading || chosen.length !== (pending.reward?.keep || 1)}>
              Guardar cartas elegidas
            </button>
          </>
        )}
      </div>
    </div>
  );
}
