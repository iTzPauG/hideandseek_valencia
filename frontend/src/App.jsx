import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useStore } from "./store";
import AuthPage from "./pages/AuthPage";
import LobbyPage from "./pages/LobbyPage";
import GamePage from "./pages/GamePage";
import RankingView from "./components/RankingView";

function Protected({ children }) {
  const token = useStore((s) => s.token);
  return token ? children : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AuthPage />} />
        <Route path="/lobby" element={<Protected><LobbyPage /></Protected>} />
        <Route path="/game/:gameId" element={<Protected><GamePage /></Protected>} />
        <Route path="/ranking" element={<Protected><RankingView /></Protected>} />
      </Routes>
    </BrowserRouter>
  );
}
