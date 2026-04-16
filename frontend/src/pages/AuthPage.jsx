import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { useStore } from "../store";

export default function AuthPage() {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const login = useStore((s) => s.login);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const payload =
        mode === "login"
          ? new URLSearchParams({ username: form.username, password: form.password })
          : form;
      const headers = mode === "login" ? { "Content-Type": "application/x-www-form-urlencoded" } : {};
      const { data } = await api.post(endpoint, payload, { headers });
      login({ id: data.user_id, username: data.username }, data.access_token);
      navigate("/lobby");
    } catch (err) {
      setError(err.response?.data?.detail || "Error");
    }
  };

  return (
    <div className="auth-page">
      <h1>🕵️ Hide & Seek Valencia</h1>
      <div className="tabs">
        <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Entrar</button>
        <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Registrarse</button>
      </div>
      <form onSubmit={submit}>
        <input placeholder="Usuario" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
        {mode === "register" && (
          <input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        )}
        <input type="password" placeholder="Contraseña" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        {error && <p className="error">{error}</p>}
        <button type="submit">{mode === "login" ? "Entrar" : "Crear cuenta"}</button>
      </form>
    </div>
  );
}
