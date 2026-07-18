import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const outfit = Outfit({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Hospitality AI Operations Assistant",
  description: "Enterprise-grade knowledge assistant for hotel operations, SOPs, and policies.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-screen w-screen overflow-hidden bg-zinc-950 text-zinc-100">
      <body className={`${outfit.className} h-screen w-screen flex p-4 gap-4 relative overflow-hidden bg-zinc-950`}>
        {/* Background Ambient Glows */}
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-indigo-900/10 rounded-full blur-[120px] pointer-events-none z-0" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-violet-900/10 rounded-full blur-[120px] pointer-events-none z-0" />
        
        <Sidebar />
        <main className="flex-1 h-full flex flex-col overflow-hidden relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
