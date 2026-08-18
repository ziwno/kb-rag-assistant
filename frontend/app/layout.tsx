import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "个人智能知识库助手",
  description: "上传 PDF/图片/音频，基于 RAG 的智能问答与摘要",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
