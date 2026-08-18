"use client";

import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage as Message } from "@/store/chatStore";

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground",
          message.error && "border border-destructive/40"
        )}
      >
        {message.content ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <span className="inline-flex items-center gap-1 text-muted-foreground">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:150ms]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:300ms]" />
          </span>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 border-t border-border/60 pt-2 text-xs text-muted-foreground">
            <span className="font-medium">引用来源: </span>
            {message.sources.map((src) => (
              <span
                key={src}
                className="mr-1 inline-block rounded bg-background px-1.5 py-0.5 text-[10px]"
              >
                {src}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
