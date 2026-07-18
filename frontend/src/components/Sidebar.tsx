"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { 
  MessageSquare, 
  FileText, 
  BarChart3, 
  Menu, 
  X, 
  Hotel,
  ShieldCheck
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { name: "AI Operations Assistant", path: "/", icon: MessageSquare },
    { name: "Document Manager", path: "/admin/documents", icon: FileText },
    { name: "System Stats & Health", path: "/admin/dashboard", icon: BarChart3 },
  ];

  return (
    <>
      {/* Mobile Toggle Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 p-2 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-md lg:hidden hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* Sidebar Wrapper */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-72 bg-zinc-900/20 border border-white/[0.04] backdrop-blur-xl rounded-2xl flex flex-col justify-between transition-transform duration-300 ease-in-out shadow-2xl
        lg:static lg:translate-x-0 lg:h-full
        ${isOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        {/* Top Header */}
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-500/80 via-indigo-600/80 to-violet-600/80 rounded-xl shadow-lg shadow-indigo-500/10 text-white border border-white/[0.06]">
              <Hotel className="h-5.5 w-5.5" />
            </div>
            <div>
              <h1 className="font-bold text-sm leading-tight tracking-wider text-white uppercase">
                AISOP Hub
              </h1>
              <p className="text-[9px] text-zinc-400 font-extrabold tracking-widest uppercase mt-0.5">Hotel Operations</p>
            </div>
          </div>
  
          {/* Nav Items */}
          <nav className="space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  onClick={() => setIsOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-bold tracking-wide uppercase transition-all duration-300 border
                    ${isActive 
                      ? "bg-white/[0.02] border-white/[0.06] text-white shadow-md shadow-black/10" 
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.01] border-transparent"
                    }
                  `}
                >
                  <Icon className={`h-4.5 w-4.5 transition-colors ${isActive ? "text-indigo-400" : "text-zinc-500"}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer Brand Info */}
        <div className="p-6 border-t border-white/[0.03] bg-zinc-950/20">
          <div className="flex items-center gap-2 text-[10px] text-zinc-550 font-bold uppercase tracking-wider">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span>Secure Mode</span>
          </div>
          <p className="text-[9px] text-zinc-600 mt-1 uppercase font-bold tracking-widest">Version 1.0.0 (Gold)</p>
        </div>
      </div>

      {/* Overlay for Mobile */}
      {isOpen && (
        <div 
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}
    </>
  );
}
