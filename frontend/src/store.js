import { create } from "zustand";

export const useStore = create((set) => ({
  user: JSON.parse(localStorage.getItem("user") || "null"),
  token: localStorage.getItem("token") || null,
  game: null,
  myRole: null, // "fugitive" | "hunter"

  login: (user, token) => {
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", token);
    set({ user, token });
  },
  logout: () => {
    localStorage.clear();
    set({ user: null, token: null, game: null, myRole: null });
  },
  setGame: (game) => {
    const userId = JSON.parse(localStorage.getItem("user") || "{}").id;
    // Derive role from the player's own role field (updated on each round change)
    const myRole = game.players?.[String(userId)]?.role || null;
    set({ game, myRole });
  },
}));
