"use client";

import { useEffect } from "react";
import {
  AudioLines,
  FileText,
  Image as ImageIcon,
  Loader2,
  RefreshCw,
  Trash2,
  Type,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, FILE_TYPE_LABELS, formatBytes, formatTime } from "@/lib/utils";
import { useChatStore } from "@/store/chatStore";
import { useFileStore } from "@/store/fileStore";

const TYPE_ICON: Record<string, React.ReactNode> = {
  pdf: <FileText className="h-4 w-4 shrink-0" />,
  image: <ImageIcon className="h-4 w-4 shrink-0" />,
  audio: <AudioLines className="h-4 w-4 shrink-0" />,
  text: <Type className="h-4 w-4 shrink-0" />,
};

const STATUS_BADGE: Record<
  string,
  { label: string; className: string }
> = {
  pending: { label: "等待中", className: "bg-muted text-muted-foreground" },
  processing: { label: "处理中", className: "bg-blue-100 text-blue-700" },
  completed: { label: "已就绪", className: "bg-green-100 text-green-700" },
  failed: { label: "失败", className: "bg-red-100 text-red-700" },
};

export function FileList() {
  const { files, loading, fetchFiles, remove } = useFileStore();
  const { selectedFileIds, toggleFile, deselectFile } = useChatStore();

  const hasActive = files.some(
    (f) => f.status === "pending" || f.status === "processing"
  );

  useEffect(() => {
    void fetchFiles();
  }, [fetchFiles]);

  // 有文件在后台处理时轮询刷新状态
  useEffect(() => {
    if (!hasActive) return;
    const timer = setInterval(() => void fetchFiles(), 3000);
    return () => clearInterval(timer);
  }, [hasActive, fetchFiles]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          我的文档 ({files.length})
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void fetchFiles()}
          disabled={loading}
          aria-label="刷新文件列表"
        >
          <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
        </Button>
      </div>

      {files.length === 0 ? (
        <p className="rounded-md border border-dashed py-6 text-center text-xs text-muted-foreground">
          还没有文档，上传后即可开始提问
        </p>
      ) : (
        <ul className="max-h-[calc(100vh-22rem)] space-y-1 overflow-y-auto pr-1">
          {files.map((file) => {
            const badge = STATUS_BADGE[file.status] ?? STATUS_BADGE.pending;
            const selected = selectedFileIds.includes(file.id);
            return (
              <li
                key={file.id}
                onClick={() => toggleFile(file.id)}
                title="点击选择/取消，作为本次问答的文档范围"
                className={cn(
                  "group cursor-pointer rounded-md border p-2 transition-colors",
                  selected
                    ? "border-primary bg-primary/5"
                    : "border-border hover:bg-accent/50"
                )}
              >
                <div className="flex items-center gap-2">
                  {TYPE_ICON[file.file_type] ?? <FileText className="h-4 w-4 shrink-0" />}
                  <span className="min-w-0 flex-1 truncate text-xs font-medium">
                    {file.filename}
                  </span>
                  <Badge className={badge.className}>{badge.label}</Badge>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      void remove(file.id);
                      // 同步清理聊天范围的选中状态，避免把已删除文件的 id 传给后端
                      deselectFile(file.id);
                    }}
                    className="rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                    aria-label={`删除 ${file.filename}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                <div className="mt-1 flex items-center gap-2 text-[10px] text-muted-foreground">
                  <span>{FILE_TYPE_LABELS[file.file_type] ?? file.file_type}</span>
                  <span>{formatBytes(file.file_size)}</span>
                  <span>{file.chunk_count > 0 ? `${file.chunk_count} 片段` : ""}</span>
                  <span>{formatTime(file.created_at)}</span>
                </div>
                {file.status === "failed" && file.error_message && (
                  <p className="mt-1 line-clamp-2 text-[10px] text-destructive">
                    失败原因: {file.error_message}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {hasActive && (
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" /> 后台解析中，请稍候...
        </p>
      )}
    </div>
  );
}
