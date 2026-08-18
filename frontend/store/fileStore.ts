import { create } from "zustand";
import { api } from "@/lib/api";

export type FileStatus = "pending" | "processing" | "completed" | "failed";

export interface KnowledgeFile {
  id: string;
  filename: string;
  file_type: string;
  file_size: number | null;
  status: FileStatus;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
}

interface FileState {
  files: KnowledgeFile[];
  loading: boolean;
  uploading: boolean;
  error: string | null;
  fetchFiles: () => Promise<void>;
  upload: (file: File, fileType?: string) => Promise<void>;
  remove: (id: string) => Promise<void>;
  resetError: () => void;
}

export const useFileStore = create<FileState>((set, get) => ({
  files: [],
  loading: false,
  uploading: false,
  error: null,

  fetchFiles: async () => {
    set({ loading: true });
    try {
      const { data } = await api.get<KnowledgeFile[]>("/files");
      set({ files: data, loading: false, error: null });
    } catch {
      set({ loading: false, error: "获取文件列表失败" });
    }
  },

  upload: async (file, fileType) => {
    const formData = new FormData();
    formData.append("file", file);
    if (fileType) formData.append("file_type", fileType);

    set({ uploading: true, error: null });
    try {
      await api.post("/files/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 0, // 大文件上传不设超时
      });
      await get().fetchFiles();
    } catch (e) {
      const detail = (e as any)?.response?.data?.detail;
      set({ error: detail ?? "上传失败，请重试" });
      throw e;
    } finally {
      set({ uploading: false });
    }
  },

  remove: async (id) => {
    await api.delete(`/files/${id}`);
    set((s) => ({ files: s.files.filter((f) => f.id !== id) }));
  },

  resetError: () => set({ error: null }),
}));
