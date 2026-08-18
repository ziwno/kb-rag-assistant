"use client";

import { useEffect, useRef } from "react";
import { Eraser, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuthStore } from "@/store/authStore";
import { useChatStore } from "@/store/chatStore";
import { useFileStore } from "@/store/fileStore";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";

export function ChatWindow() {
  const { messages, streaming, selectedFileIds, summarize, clear } = useChatStore();
  const token = useAuthStore((s) => s.token);
  const files = useFileStore((s) => s.files);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const canSummarize =
    selectedFileIds.length > 0 && !streaming;

  return (
    <Card className="flex h-full min-h-0 flex-col overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold">智能问答</h2>
          <p className="text-xs text-muted-foreground">
            {selectedFileIds.length > 0
              ? `当前问答范围: 已选 ${selectedFileIds.length} 个文档`
              : "当前问答范围: 全部文档"}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            disabled={!canSummarize}
            onClick={() => void summarize(selectedFileIds, token)}
            title="对选中文档生成摘要"
          >
            <Sparkles className="h-3.5 w-3.5" />
            生成摘要
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clear}
            title="清空对话"
            disabled={messages.length === 0}
          >
            <Eraser className="h-3.5 w-3.5" />
            清空
          </Button>
        </div>
      </div>

      {/* 消息区 */}
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <Sparkles className="h-10 w-10 text-primary/60" />
            <p className="text-sm font-medium text-foreground">
              基于你的知识库回答问题
            </p>
            <p className="max-w-sm text-xs text-muted-foreground">
              上传 PDF / 图片 / 音频 / 文本后，直接提问即可。左侧点击文档可限定本次问答的范围，也可一键生成摘要。
            </p>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* 输入区 */}
      <ChatInput disabled={streaming} onFilesSelected={files.length === 0} />
    </Card>
  );
}
