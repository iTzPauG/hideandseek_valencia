import { useEffect, useState } from "react";
import api from "../api";

const CATEGORY_LABELS = { radar: "📡 Radar", match: "🔗 Match", photo: "📷 Foto" };

const STADIUMS = [
  { name: "Mestalla", lat: 39.4747, lon: -0.3583 },
  { name: "Nou Mestalla", lat: 39.4894, lon: -0.3964 },
  { name: "Estadi Ciutat de València", lat: 39.4947, lon: -0.3642 },
  { name: "Roig Arena", lat: 39.4492, lon: -0.3642 },
];

export default function QuestionsView({ game, gameId, onShowMap, onPreviewRadar, onPreviewStadiums }) {
  const [questions, setQuestions] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [confirm, setConfirm] = useState(null); // question to confirm
  const used = game.used_questions || [];
  const radarResult = game.radar_pending_result;
  const pending = game.pending_question;

  useEffect(() => {
    api.get("/questions/list").then(({ data }) => setQuestions(data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (pending?.status === "answered" && result?.pending) {
      setResult({ ...result, answer: pending.answer, pending: false });
    }
    if (pending?.status === "vetoed" && result?.pending) {
      setResult({ ...result, answer: "vetoed", pending: false });
    }
  }, [pending?.status]);

  const dismissRadar = async () => {
    await api.post("/questions/dismiss-radar-result", { game_id: gameId });
    onShowMap && onShowMap();
  };

  const ask = async (q) => {
    setConfirm(null);
    setLoading(true);
    try {
      const body = { game_id: gameId, question_id: q.id };
      if (q.category === "radar") body.radar_radius_m = q.radar_radius_m || 1000;
      const { data } = await api.post("/questions/ask", body);
      setResult({ question: q, ...data });
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    } finally {
      setLoading(false);
    }
  };

  const byCategory = questions.reduce((acc, q) => {
    (acc[q.category] = acc[q.category] || []).push(q);
    return acc;
  }, {});

  const renderAnswer = () => {
    if (result?.answer === "vetoed") return "🚫 Vetada por el fugitivo";
    if (result?.answer === true) return "✅ SÍ";
    if (result?.answer === false) return "❌ NO";
    if (result?.pending) return "⏳ Esperando respuesta del fugitivo...";
    return "—";
  };

  const hunterLat = game.players ? Object.values(game.players).find(p => p.role === "hunter")?.lat : null;
  const hunterLon = game.players ? Object.values(game.players).find(p => p.role === "hunter")?.lon : null;

  return (
    <div className="questions-view">
      {/* Radar result popup */}
      {radarResult && (
        <div className="radar-result-popup">
          <div className={`radar-result-box ${radarResult.answer ? "hit" : "miss"}`}>
            <div className="radar-result-title">
              {radarResult.answer ? "🎯 IT'S A HIT!" : "💨 IT'S A MISS"}
            </div>
            <div className="radar-result-sub">
              {radarResult.stadium
                ? `Estadio: ${radarResult.stadium}`
                : radarResult.turia_dist != null
                ? `Turia: cazador a ${radarResult.turia_dist}m`
                : `Radio: ${radarResult.radius_m >= 1000 ? `${radarResult.radius_m/1000}km` : `${radarResult.radius_m}m`}`}
            </div>
            <button className="pq-btn primary" onClick={dismissRadar}>🗺️ Mostrar en mapa</button>
          </div>
        </div>
      )}

      {/* Confirm popup */}
      {confirm && (
        <div className="radar-result-popup">
          <div className="radar-result-box" style={{ borderTop: '2px solid #e63946' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>¿Estás seguro?</div>
            <div style={{ color: '#aaa', fontSize: '0.9rem', marginBottom: '1rem' }}>{confirm.title}</div>
            <button className="pq-btn primary" onClick={() => ask(confirm)} disabled={loading}>
              ✅ Enviar pregunta
            </button>
            <button className="pq-btn" style={{ marginTop: '0.5rem' }} onClick={() => setConfirm(null)}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      {result && (
        <div className="result-banner">
          <strong>{result.question.title}</strong>: {renderAnswer()}
          <button onClick={() => setResult(null)}>✕</button>
        </div>
      )}

      {Object.entries(byCategory).map(([cat, qs]) => (
        <details key={cat} open>
          <summary>{CATEGORY_LABELS[cat] || cat}</summary>
          {qs
            .sort((a, b) => used.includes(a.id) - used.includes(b.id))
            .map((q) => {
              const isUsed = used.includes(q.id);
              const isRadar = q.category === "radar";
              const isStadium = q.id === "match_stadium";
              const isTuria = q.id === "match_turia";
              return (
                <div key={q.id} className={`question-item ${isUsed ? "used" : ""}`}>
                  <div style={{ flex: 1 }}>
                    <strong>{q.title}</strong>
                    <p>{q.description}</p>
                  </div>
                  <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.4rem' }}>
                    {(isRadar || isStadium || isTuria) && !isUsed && (
                      <button className="q-preview-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (isRadar && hunterLat && onPreviewRadar) {
                            onPreviewRadar({ hunter_lat: hunterLat, hunter_lon: hunterLon, radar_radius_m: q.radar_radius_m || 1000 });
                          } else if (isStadium && onPreviewStadiums) {
                            onPreviewStadiums(STADIUMS);
                          } else if (isTuria && onPreviewStadiums) {
                            onPreviewStadiums({ previewType: 'turia_hunter' });
                          }
                        }}>
                        👁 Mostrar
                      </button>
                    )}
                    {!isUsed && (
                      <button className="q-ask-btn"
                        onClick={(e) => { e.stopPropagation(); !loading && setConfirm(q); }}>
                        Preguntar
                      </button>
                    )}
                    {isUsed && <span className="badge">Usada</span>}
                  </div>
                </div>
              );
            })}
        </details>
      ))}
      {loading && <div className="loading-overlay">Enviando pregunta...</div>}
    </div>
  );
}
