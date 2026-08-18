"use client";

import { useRef, useState } from "react";
import { Loader2, UploadCloud, X } from "lucide-react";
import { useFileStore } from "@/store/fileStore";

const ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.gif,.webp,.bmp,.mp3,.wav,.m4a,.ogg,.flac,.aac,.txt,.md";

export function FileUploader() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { upload, uploading, error, resetError } = useFileStore();
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    for (const file of Array.from(files)) {
      try {
        await upload(file);
      } catch {
        // 错误已记录到 store，这里继续上传剩余文件
      }
    }
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          void handleFiles(e.dataTransfer.files);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          dragOver
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50"
        }`}
      >
        {uploading ? (
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        ) : (
          <UploadCloud className="h-8 w-8 text-muted-foreground" />
        )}
        <p className="text-sm font-medium">
          {uploading ? "正在上传..." : "点击选择文件或拖拽到此处"}
        </p>
        <p className="text-xs text-muted-foreground">
          支持 PDF / 图片 / 音频 / 文本，单个最大 100MB，可多选
        </p>
        <input
          ref={inputRef}
          type="file"
          hidden
          multiple
          accept={ACCEPT}
          onChange={(e) => void handleFiles(e.target.files)}
        />
      </div>

      {error && (
        <div className="mt-2 flex items-center justify-between rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          <span className="line-clamp-2">{error}</span>
          <button
            onClick={resetError}
            className="ml-2 shrink-0 rounded p-1 hover:bg-destructive/10"
            aria-label="关闭错误提示"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
