import { API_BASE_URL } from "./api";

export interface StreamEvent {
  type: "start" | "content" | "end" | "error";
  chunk?: string;
  sources?: string[];
}

export interface StreamHandlers {
  onContent: (chunk: string) => void;
  onEnd: (sources: string[]) => void;
  onError: (message: string) => void;
  signal?: AbortSignal;
}

/**
 * 通过 fetch 消费 SSE 流 (fetch 能带 Authorization 头，EventSource 不能)。
 * 后端事件格式: data: {json}\n\n，`: ping` 行是心跳，直接跳过。
 */
export async function streamChat(
  question: string,
  fileIds: string[],
  token: string | null,
  handlers: StreamHandlers
): Promise<void> {
  const url = new URL(`${API_BASE_URL}/api/chat/stream`);
  url.searchParams.set("question", question);
  if (fileIds.length) url.searchParams.set("file_ids", fileIds.join(","));

  const res = await fetch(url.toString(), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    signal: handlers.signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`请求失败 (${res.status}): ${text.slice(0, 200)}`);
  }
  if (!res.body) throw new Error("当前浏览器不支持流式响应");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 帧以空行分隔
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data:")) continue; // 心跳注释行
      const data = line.slice(5).trim();
      if (data === "[DONE]") continue;

      try {
        const event = JSON.parse(data) as StreamEvent;
        if (event.type === "content") handlers.onContent(event.chunk ?? "");
        else if (event.type === "end") handlers.onEnd(event.sources ?? []);
        else if (event.type === "error") handlers.onError(event.chunk ?? "生成失败");
      } catch {
        // 忽略无法解析的帧
      }
    }
  }
}
