import { useEffect, useState, useCallback } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline, Circle, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import api from "../api";
import { useStore } from "../store";

const LINE_COLORS = {
  "1": "#FFD700", "2": "#CC44CC", "3": "#E74C3C", "4": "#2980B9",
  "5": "#27AE60", "6": "#8E44AD", "7": "#E67E22", "8": "#3498DB",
  "9": "#795548", "10": "#2ECC71",
};

function offsetSegment(p1, p2, idx, offsetDeg) {
  if (idx === 0) return [p1, p2];
  const dlat = p2[0] - p1[0];
  const dlon = p2[1] - p1[1];
  const len = Math.sqrt(dlat * dlat + dlon * dlon) || 1;
  const nx = -dlon / len;
  const ny = dlat / len;
  const d = offsetDeg * idx;
  return [
    [p1[0] + nx * d, p1[1] + ny * d],
    [p2[0] + nx * d, p2[1] + ny * d],
  ];
}

function Lines({ lines, stationMap }) {
  const map = useMap();
  const [zoom, setZoom] = useState(map.getZoom());
  useEffect(() => {
    const h = () => setZoom(map.getZoom());
    map.on("zoomend", h);
    return () => map.off("zoomend", h);
  }, [map]);

  // offset in degrees: ~5px at current zoom
  const metersPerPx = 156543.03392 * Math.cos(39.47 * Math.PI / 180) / Math.pow(2, zoom);
  const offsetDeg = (metersPerPx * 5) / 111320;

  const segLines = {};
  for (const line of lines) {
    const ids = line.station_ids || [];
    for (let i = 0; i < ids.length - 1; i++) {
      const key = [ids[i], ids[i + 1]].sort().join("|");
      if (!segLines[key]) segLines[key] = [];
      const lid = line.id;
      if (!segLines[key].includes(lid)) segLines[key].push(lid);
    }
  }

  const elements = [];
  for (const line of lines) {
    const ids = line.station_ids || [];
    const color = LINE_COLORS[line.id] || "#888";
    for (let i = 0; i < ids.length - 1; i++) {
      const s1 = stationMap[ids[i]];
      const s2 = stationMap[ids[i + 1]];
      if (!s1 || !s2) continue;
      const key = [ids[i], ids[i + 1]].sort().join("|");
      const shared = segLines[key];
      const myIdx = shared.indexOf(line.id);
      const centred = myIdx - (shared.length - 1) / 2;
      const [op1, op2] = offsetSegment([s1.lat, s1.lon], [s2.lat, s2.lon], centred, offsetDeg);
      elements.push(
        <Polyline key={`${line.id}-${i}`} positions={[op1, op2]}
          color={color} weight={4} opacity={0.9} />
      );
    }
  }
  return <>{elements}</>;
}

function LocateButton() {
  const map = useMap();
  const locate = useCallback(() => {
    navigator.geolocation?.getCurrentPosition((p) => {
      map.setView([p.coords.latitude, p.coords.longitude], 15, { animate: true });
    });
  }, [map]);
  return (
    <button className="locate-btn" onClick={locate} title="Mi ubicación">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4A90E2" strokeWidth="2.5">
        <circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" strokeDasharray="2 2"/>
        <line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/>
        <line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/>
      </svg>
    </button>
  );
}

function OwnLocationMarker() {
  const [pos, setPos] = useState(null);
  const [accuracy, setAccuracy] = useState(0);

  useEffect(() => {
    if (!navigator.geolocation) return;
    const id = navigator.geolocation.watchPosition(
      (p) => { setPos([p.coords.latitude, p.coords.longitude]); setAccuracy(p.coords.accuracy); },
      () => {},
      { enableHighAccuracy: true, maximumAge: 10000 }
    );
    return () => navigator.geolocation.clearWatch(id);
  }, []);

  if (!pos) return null;
  return (
    <>
      <Circle center={pos} radius={accuracy} color="#4A90E2" fillColor="#4A90E2" fillOpacity={0.1} weight={1} />
      <CircleMarker center={pos} radius={10} color="#fff" weight={2} fillColor="#4A90E2" fillOpacity={1}>
        <Popup>📍 Tu ubicación</Popup>
      </CircleMarker>
    </>
  );
}

export default function MapView({ game, myRole, gameId }) {
  const [stations, setStations] = useState([]);
  const [lines, setLines] = useState([]);
  const [pendingStation, setPendingStation] = useState(null);
  const user = useStore((s) => s.user);

  useEffect(() => {
    api.get("/map/stations").then(({ data }) => setStations(data));
    api.get("/map/lines").then(({ data }) => setLines(data));
  }, []);

  const confirmHide = async () => {
    try {
      await api.post("/players/select-station", { game_id: gameId, station_id: pendingStation.id });
      setPendingStation(null);
    } catch (err) {
      alert(err.response?.data?.detail || "No puedes esconderte aquí");
      setPendingStation(null);
    }
  };

  const players = game.players || {};
  const discarded = game.discarded_stations || [];
  const fugitiveStation = game.fugitive_station;
  const hideRadius = game.hide_radius_m || 150;
  const lineStationIds = new Set(lines.flatMap(l => l.station_ids || []));
  const visibleStations = stations.filter(s => lineStationIds.has(s.id));
  const stationMap = Object.fromEntries(stations.map(s => [s.id, s]));

  return (
    <>
      {pendingStation && (
        <div className="station-confirm-overlay">
          <div className="station-confirm-box">
            <p>¿Esconderte en <strong>{pendingStation.name}</strong>?</p>
            <div className="station-confirm-btns">
              <button className="btn-confirm" onClick={confirmHide}>✅ Sí, esconderme aquí</button>
              <button className="btn-cancel" onClick={() => setPendingStation(null)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}

      <MapContainer center={[39.4699, -0.3763]} zoom={12}
        style={{ height: "calc(100vh - 140px)", width: "100%" }}>
        <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" attribution="© OpenStreetMap © CARTO" />

        <Lines lines={lines} stationMap={stationMap} />

        {visibleStations.map((st) => {
          const isDiscarded = discarded.includes(st.id);
          const isHideout = myRole === "fugitive" && fugitiveStation === st.id;
          const numLines = (st.lines || []).length;
          const radius = numLines >= 4 ? 8 : numLines >= 2 ? 6 : 5;
          const fillColor = isDiscarded ? "#555" : isHideout ? "#00e676" : "#fff";
          return (
            <CircleMarker key={st.id} center={[st.lat, st.lon]}
              radius={radius} color="#222" fillColor={fillColor} fillOpacity={1} weight={1.5}
              eventHandlers={{ click: () => myRole === "fugitive" && game.status === "hiding" && setPendingStation(st) }}>
              <Popup>
                <strong>{st.name}</strong><br />
                {(st.lines || []).map(id => (
                  <span key={id} style={{ color: LINE_COLORS[id], fontWeight: "bold", marginRight: 4 }}>L{id}</span>
                ))}
              </Popup>
            </CircleMarker>
          );
        })}

        {myRole === "fugitive" && fugitiveStation && stationMap[fugitiveStation] && (
          <Circle center={[stationMap[fugitiveStation].lat, stationMap[fugitiveStation].lon]}
            radius={hideRadius} color="#00e676" fillOpacity={0.1} />
        )}

        {Object.entries(players).map(([pid, p]) => {
          if (!p.lat || pid === String(user?.id)) return null;
          if (myRole === "hunter") return null;
          return (
            <CircleMarker key={pid} center={[p.lat, p.lon]} radius={9}
              color="#fff" weight={2} fillColor="#E74C3C" fillOpacity={0.9}>
              <Popup>{p.username}</Popup>
            </CircleMarker>
          );
        })}

        <OwnLocationMarker />
        <LocateButton />
      </MapContainer>
    </>
  );
}
