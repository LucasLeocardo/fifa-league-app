import { create } from "zustand";

export type FlashVariant = "success" | "error";

type FlashState = {
  message: string | null;
  variant: FlashVariant;
  show: (message: string, variant: FlashVariant) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  clear: () => void;
};

export const useFlashStore = create<FlashState>((set) => ({
  message: null,
  variant: "success",
  show: (message, variant) => set({ message, variant }),
  success: (message) => set({ message, variant: "success" }),
  error: (message) => set({ message, variant: "error" }),
  clear: () => set({ message: null }),
}));
