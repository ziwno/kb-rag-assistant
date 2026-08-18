"use client";

import { useState } from "react";
import { Loader2, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/store/authStore";
import { useChatStore } from "@/store/chatStore";

export function ChatInput({
  disabled,
  onFilesSelected,
}: {
  disabled: boolean;
  onFilesSelected: boolean;
}) {
  const [value, setValue] = useState("");
  const { send, streaming } = useChatStore();
  const token = useAuthStore((s) => s.token);

  const submit = () => {
    const question = value.trim();
    if (!question || streaming) return;
    void send(question, token);
    setValue("");
  };

  return (
    <div className="border-t p-3">
      {onFilesSelected && (
        <p className="mb-2 text-center text-xs text-amber-600">
          提示: 知识库中还没有文档，请先上传文件
        </p>
      )}
      <div className="flex items-end gap-2">
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="基于知识库提问，Enter 发送，Shift+Enter 换行"
          rows={2}
          disabled={disabled}
          className="min-h-[60px] max-h-40 resize-none"
        />
        <Button
          onClick={submit}
          disabled={disabled || !value.trim() || streaming}
          size="icon"
          aria-label="发送"
        >
          {streaming ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
