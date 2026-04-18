const MEDALS = ["🥇", "🥈", "🥉"];
const MEDAL_COLORS = ["#FFD700", "#C0C0C0", "#CD7F32"];

const fmt = (s) => {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${sec}s` : `${sec}s`;
};

export default function RankingView({ game }) {
  const scores = game?.scores || {};
  const players = game?.players || {};
  const ranking = Object.entries(scores)
    .map(([pid, secs]) => ({ username: players[pid]?.username || `Jugador ${pid}`, secs }))
    .sort((a, b) => b.secs - a.secs);

  return (
    <div className="ranking-view">
      <h3>🏆 Ranking</h3>
      {ranking.length === 0 && <p style={{ color: '#aaa' }}>Aún no hay rondas completadas</p>}
      <ol className="ranking-list">
        {ranking.map((r, i) => (
          <li key={r.username} className="ranking-item">
            <span className="rank-medal" style={{ color: MEDAL_COLORS[i] || "#aaa" }}>
              {MEDALS[i] || `${i+1}`}
            </span>
            <span className="rank-name">{r.username}</span>
            <span className="rank-time">{fmt(r.secs)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
