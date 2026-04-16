import { useEffect, useState } from "react";

function elapsed(isoStart) {
  const diff = Math.max(0, Date.now() - new Date(isoStart).getTime());
  const m = Math.floor(diff / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function countdown(isoStart, limitMin) {
  const end = new Date(isoStart).getTime() + limitMin * 60000;
  const diff = Math.max(0, end - Date.now());
  const m = Math.floor(diff / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function Timer({ game, role }) {
  const [, tick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const status = game?.status;
  const hideStart = game?.hide_start;
  const huntStart = game?.hunt_start;

  return (
    <div className="timer-bar">
      <span className="role-badge">{role === "fugitive" ? "🏃 Fugitivo" : role === "hunter" ? "🕵️ Cazador" : ""}</span>
      {status === "hiding" && hideStart && (
        <span>Escondite: <strong>{countdown(hideStart, 30)}</strong></span>
      )}
      {status === "hunting" && huntStart && (
        <span>Cazando: <strong>{elapsed(huntStart)}</strong></span>
      )}
      {status === "waiting" && <span>⏳ Esperando...</span>}
      {status === "round_end" && <span>✅ Ronda terminada</span>}
      {status === "finished" && <span>🏁 Partida terminada</span>}
    </div>
  );
}
