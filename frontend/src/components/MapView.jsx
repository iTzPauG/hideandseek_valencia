import React, { useEffect, useState, useCallback } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline, Circle, Polygon, Rectangle, SVGOverlay, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import api from "../api";
import { useStore } from "../store";

const LINE_COLORS = {
  "1": "#FFD700", "2": "#CC44CC", "3": "#E74C3C", "4": "#2980B9",
  "4b": "#2980B9", "4c": "#2980B9", "4d": "#2980B9",
  "5": "#27AE60", "6": "#8E44AD", "7": "#E67E22", "8": "#3498DB",
  "9": "#795548", "10": "#2ECC71",
};

// Fixed global order — determines which side each line sits on shared segments
const LINE_ORDER = ["1","2","3","4","5","6","7","8","9","10"];

// Segments where the canonical N→S perpendicular points the wrong way — pre-computed
const FLIP_SEGMENTS = new Set([
  "paiporta|picanya","picanya|torrent",
  "angel_guimera|xativa",
  "av_cid|nou_octubre","mislata|nou_octubre","mislata|mislata_almassil","faitanar|mislata_almassil",
  "faitanar|quart_poblet","quart_poblet|salt_aigua","manises|salt_aigua","manises|rosas",
  "benimaclet|trinitat","benimaclet|vicent_zaragoza","univ_politecnica|vicent_zaragoza",
  "la_carrasca|univ_politecnica","la_carrasca|tarongers","betero|tarongers",
  "betero|la_cadena","cabanyal|la_cadena","la_cadena|platja_malva_rosa","platja_les_arenes|platja_malva_rosa",
  "alameda|aragon","amistat|aragon","amistat|ayora","ayora|maritim",
  "francesc_cubells|grau_marina","francesc_cubells|maritim",
]);

function Lines({ lines, stationMap }) {
  const segLines = {};
  for (const line of lines) {
    const nid = line.id.replace(/[a-z]+$/, '');
    for (let i = 0; i < (line.station_ids || []).length - 1; i++) {
      const key = [line.station_ids[i], line.station_ids[i+1]].sort().join("|");
      if (!segLines[key]) segLines[key] = [];
      if (!segLines[key].includes(nid)) segLines[key].push(nid);
    }
  }
  for (const key in segLines) {
    segLines[key].sort((a,b) => LINE_ORDER.indexOf(a) - LINE_ORDER.indexOf(b));
  }

  const offsetDeg = 0.00018;
  const elements = [];

  for (const line of lines) {
    const ids = line.station_ids || [];
    const nid = line.id.replace(/[a-z]+$/, '');
    const color = LINE_COLORS[line.id] || "#888";

    // Compute offset point for each station using miter intersection of adjacent segments
    const pts = [];
    for (let i = 0; i < ids.length; i++) {
      const s = stationMap[ids[i]];
      if (!s) { pts.push(null); continue; }

      const hasPrev = i > 0 && stationMap[ids[i-1]];
      const hasNext = i < ids.length-1 && stationMap[ids[i+1]];

      const getOff = (iA, iB) => {
        const key = [ids[iA], ids[iB]].sort().join("|");
        const shared = segLines[key] || [nid];
        const centred = shared.indexOf(nid) - (shared.length-1)/2;
        const [ka, kb] = key.split("|");
        const sa = stationMap[ka], sb = stationMap[kb];
        const [sf, st] = sa.lat >= sb.lat ? [sa, sb] : [sb, sa];
        const cosLat = Math.cos(sf.lat * Math.PI / 180);
        const dlat = st.lat-sf.lat, dlon = (st.lon-sf.lon)*cosLat;
        const len = Math.sqrt(dlat*dlat+dlon*dlon)||1;
        const flip = FLIP_SEGMENTS.has(key) ? -1 : 1;
        return [(-dlon/len)*centred*offsetDeg*flip, (dlat/len)*centred*offsetDeg/cosLat*flip];
      };

      if (hasPrev && hasNext) {
        const [nx1, ny1] = getOff(i-1, i);
        const [nx2, ny2] = getOff(i, i+1);
        // Miter: average the two offset vectors (works well for small angles)
        pts.push([s.lat + (nx1+nx2)/2, s.lon + (ny1+ny2)/2]);
      } else if (hasPrev) {
        const [nx, ny] = getOff(i-1, i);
        pts.push([s.lat+nx, s.lon+ny]);
      } else if (hasNext) {
        const [nx, ny] = getOff(i, i+1);
        pts.push([s.lat+nx, s.lon+ny]);
      } else {
        pts.push([s.lat, s.lon]);
      }
    }

    const positions = pts.filter(Boolean);
    if (positions.length >= 2) {
      elements.push(
        <Polyline key={line.id} positions={positions}
          color={color} weight={4} opacity={0.9}
          pathOptions={{ lineCap: 'round', lineJoin: 'round' }} />
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

export default function MapView({ game, myRole, gameId, radarPreview }) {
  const [stations, setStations] = useState([]);
  const [lines, setLines] = useState([]);
  const [pendingStation, setPendingStation] = useState(null);
  const user = useStore((s) => s.user);

  useEffect(() => {
    const t = Date.now();
    api.get(`/map/stations?_t=${t}`).then(({ data }) => setStations(data));
    api.get(`/map/lines?_t=${t}`).then(({ data }) => setLines(data));
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
                  <span key={id} style={{ color: LINE_COLORS[id] || LINE_COLORS[id.replace(/[a-z]+$/,"")], fontWeight: "bold", marginRight: 4 }}>L{id.replace(/[a-z]+$/,"")}</span>
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

        {/* Radar overlays — accumulated, visible to all */}
        {(game.radar_overlays || []).map((o, i) => {
          if (!o.inside) return (
            <Circle key={i} center={[o.hunter_lat, o.hunter_lon]} radius={o.radius_m}
              pathOptions={{ color:'#e74c3c', weight:3, fillColor:'#e74c3c', fillOpacity:0.25 }} />
          );
          // Build donut polygon: outer box + inner circle hole
          const outer = [
            [o.hunter_lat+2, o.hunter_lon-3],
            [o.hunter_lat+2, o.hunter_lon+3],
            [o.hunter_lat-2, o.hunter_lon+3],
            [o.hunter_lat-2, o.hunter_lon-3],
          ];
          const steps = 64;
          const latR = o.radius_m / 111000;
          const lonR = o.radius_m / (111000 * Math.cos(o.hunter_lat * Math.PI / 180));
          const hole = Array.from({length: steps}, (_, k) => {
            const a = (2 * Math.PI * k) / steps;
            return [o.hunter_lat + latR * Math.sin(a), o.hunter_lon + lonR * Math.cos(a)];
          });
          return (
            <Polygon key={i} positions={[outer, hole]}
              pathOptions={{ color:'#e74c3c', weight:2, fillColor:'#e74c3c', fillOpacity:0.25, fillRule:'evenodd' }} />
          );
        })}
        {radarPreview && (
          <Circle center={[radarPreview.hunter_lat, radarPreview.hunter_lon]}
            radius={radarPreview.radar_radius_m}
            pathOptions={{ color:'#e74c3c', weight:2, fill:false, dashArray:'6' }} />
        )}
      </MapContainer>
    </>
  );
}
