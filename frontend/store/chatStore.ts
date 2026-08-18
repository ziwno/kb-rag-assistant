import { create } from "zustand";
import { api } from "@/lib/api";
import { streamChat } from "@/lib/sse";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  error?: boolean;
  createdAt: string;
}

let idCounter = 0;
const nextId = () => `msg-${Date.now()}-${idCounter++}`;

interface ChatState {
  messages: ChatMessage[];
  selectedFileIds: string[];
  streaming: boolean;
  addMessage: (
    role: "user" | "assistant",
    content: string,
    opts?: { sources?: string[]; error?: boolean }
  ) => void;
  appendToLast: (chunk: string) => void;
  finishLast: (sources?: string[]) => void;
  markLastError: (message: string) => void;
  send: (question: string, token: string | null) => Promise<void>;
  summarize: (fileIds: string[], token: string | null) => Promise<void>;
  toggleFile: (fileId: string) => void;
  deselectFile: (fileId: string) => void;
  clear: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  selectedFileIds: [],
  streaming: false,

  addMessage: (role, content, opts) =>
    set((s) => ({
      messages: [
        ...s.messages,
        {
          id: nextId(),
          role,
          content,
          sources: opts?.sources,
          error: opts?.error,
          createdAt: new Date().toISOString(),
        },
      ],
    })),

  appendToLast: (chunk) =>
    set((s) => {
      if (!chunk) return s;
      const messages = [...s.messages];
      const last = messages[messages.length - 1];
      if (last) messages[messages.length - 1] = { ...last, content: last.content + chunk };
      return { messages };
    }),

  finishLast: (sources) =>
    set((s) => {
      const messages = [...s.messages];
      const last = messages[messages.length - 1];
      if (last) messages[messages.length - 1] = { ...last, sources };
      return { messages };
    }),

  markLastError: (message) =>
    set((s) => {
      const messages = [...s.messages];
      const last = messages[messages.length - 1];
      if (last)
        messages[messages.length - 1] = { ...last, content: message, error: true };
      return { messages };
    }),

  toggleFile: (fileId) =>
    set((s) => ({
      selectedFileIds: s.selectedFileIds.includes(fileId)
        ? s.selectedFileIds.filter((id) => id !== fileId)
        : [...s.selectedFileIds, fileId],
    })),

  deselectFile: (fileId) =>
    set((s) => ({
      selectedFileIds: s.selectedFileIds.filter((id) => id !== fileId),
    })),

  clear: () => set({ messages: [], selectedFileIds: [] }),

  send: async (question, token) => {
    if (get().streaming) return;
    set({ streaming: true });
    get().addMessage("user", question);
    get().addMessage("assistant", "");

    try {
      await streamChat(question, get().selectedFileIds, token, {
        onContent: (chunk) => get().appendToLast(chunk),
        onEnd: (sources) => get().finishLast(sources),
        onError: (message) => get().markLastError(message),
      });
    } catch (e) {
      get().markLastError(e instanceof Error ? e.message : "请求失败，请重试");
    } finally {
      set({ streaming: false });
    }
  },

  summarize: async (fileIds, token) => {
    if (get().streaming) return;
    set({ streaming: true });
    get().addMessage("user", "请生成所选文档的摘要");
    get().addMessage("assistant", "");

    try {
      const { data } = await api.post<{ answer: string; sources: string[] }>(
        "/summarize",
        { file_ids: fileIds }
      );
      get().appendToLast(data.answer);
      get().finishLast(data.sources);
    } catch (e) {
      get().markLastError(e instanceof Error ? e.message : "摘要生成失败");
    } finally {
      set({ streaming: false });
    }
  },
}));
