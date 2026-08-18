"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Brain, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatWindow } from "@/components/ChatWindow";
import { FileList } from "@/components/FileList";
import { FileUploader } from "@/components/FileUploader";
import { useAuthStore } from "@/store/authStore";

export default function DashboardPage() {
  const router = useRouter();
  const { token, user, logout } = useAuthStore();

  // 未登录跳转到登录页 (仅客户端执行)
  useEffect(() => {
    if (!token) router.replace("/login");
  }, [token, router]);

  if (!token) return null;

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between border-b px-4">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          <span className="font-semibold">个人智能知识库助手</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{user?.username}</span>
          <Button variant="outline" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4" />
            退出
          </Button>
        </div>
      </header>

      <main className="flex min-h-0 flex-1">
        {/* 左侧: 上传 + 文件列表 */}
        <aside className="flex w-80 shrink-0 flex-col gap-4 overflow-y-auto border-r p-4">
          <FileUploader />
          <FileList />
        </aside>

        {/* 右侧: 对话 */}
        <section className="min-h-0 flex-1 p-4">
          <ChatWindow />
        </section>
      </main>
    </div>
  );
}
