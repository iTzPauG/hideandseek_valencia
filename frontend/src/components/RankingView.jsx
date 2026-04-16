import { useEffect, useState } from "react";
import api from "../api";

export default function RankingView() {
  const [ranking, setRanking] = useState([]);

  useEffect(() => {
    api.get("/players/ranking").then(({ data }) => setRanking(data)).catch(() => {});
  }, []);

  const fmt = (s) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <div className="ranking-view">
      <h3>🏆 Ranking global</h3>
      {ranking.length === 0 && <p>Aún no hay partidas registradas</p>}
      <ol>
        {ranking.map((r, i) => (
          <li key={r.username}>
            <span className="rank-pos">{i + 1}</span>
            <span className="rank-name">{r.username}</span>
            <span className="rank-time">{fmt(r.total_seconds)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
