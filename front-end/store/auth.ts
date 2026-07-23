import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AuthSession = {
  accessToken: string;
  refreshToken: string;
  name: string;
  isAdmin: boolean;
  coachName: string | null;
  numberOfTitles: number;
};

type AuthStore = {
  accessToken: string | null;
  refreshToken: string | null;
  name: string | null;
  isAdmin: boolean;
  coachName: string | null;
  numberOfTitles: number;
  setSession: (session: AuthSession) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  clearSession: () => void;
};

const emptySession = {
  accessToken: null as string | null,
  refreshToken: null as string | null,
  name: null as string | null,
  isAdmin: false,
  coachName: null as string | null,
  numberOfTitles: 0,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      ...emptySession,
      setSession: (session) =>
        set({
          accessToken: session.accessToken,
          refreshToken: session.refreshToken,
          name: session.name,
          isAdmin: session.isAdmin,
          coachName: session.coachName,
          numberOfTitles: session.numberOfTitles,
        }),
      setTokens: (accessToken, refreshToken) =>
        set({ accessToken, refreshToken }),
      clearSession: () => set({ ...emptySession }),
    }),
    {
      name: "fifa-league-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        name: state.name,
        isAdmin: state.isAdmin,
        coachName: state.coachName,
        numberOfTitles: state.numberOfTitles,
      }),
    },
  ),
);
