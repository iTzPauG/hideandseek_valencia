import { useEffect, useState } from "react";
import api from "../api";

const CATEGORY_LABELS = { radar: "📡 Radar", match: "🔗 Match", photo: "📷 Foto" };

export default function QuestionsView({ game, gameId }) {
  const [questions, setQuestions] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const used = game.used_questions || [];
  const pending = game.pending_question;

  useEffect(() => {
    api.get("/questions/list").then(({ data }) => setQuestions(data)).catch(() => {});
  }, []);

  // Watch for pending question being answered
  useEffect(() => {
    if (pending?.status === "answered" && result?.pending) {
      setResult({ ...result, answer: pending.answer, pending: false });
    }
    if (pending?.status === "vetoed" && result?.pending) {
      setResult({ ...result, answer: "vetoed", pending: false });
    }
  }, [pending?.status]);

  const ask = async (q) => {
    if (used.includes(q.id)) return;
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

  return (
    <div className="questions-view">
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
              return (
                <div key={q.id} className={`question-item ${isUsed ? "used" : ""}`}
                  onClick={() => !isUsed && !loading && ask(q)}>
                  <strong>{q.title}</strong>
                  <p>{q.description}</p>
                  {isUsed && <span className="badge">Usada</span>}
                </div>
              );
            })}
        </details>
      ))}
      {loading && <div className="loading-overlay">Enviando pregunta...</div>}
    </div>
  );
}
