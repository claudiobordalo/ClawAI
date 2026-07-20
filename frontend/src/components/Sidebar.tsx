/**
 * Sidebar - left navigation rail with icons for all ClawAI modules.
 */

import { useApp, type PanelId } from "../context/AppContext";
import React from "react";
import { 
  FaCommentDots, 
  FaFolderOpen, 
  FaFileCode, 
  FaTerminal, 
  FaBrain, 
  FaRobot, 
  FaChartBar, 
  FaBolt, 
  FaCompressAlt,
} from "react-icons/fa";

/* ---------- NavItem (icon-only button) ---------- */

interface NavItemProps {
  icon: React.ReactNode;
  label?: string;
  active?: boolean;
  onClick?: () => void;
}

function NavItem({ icon, label, active = false, onClick }: NavItemProps): JSX.Element {
  return (
    <div
      title={label || ""}
      style={{
        width: 40, 
        height: 36, 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "center",
        cursor: "pointer", 
        borderRadius: 8, 
        marginBottom: 2, 
        position: "relative" as const,
        background: active ? "#7c3aed20" : "transparent", 
        color: active ? "#a78bfa" : "#6e7481",
      }}
      onClick={onClick}
    >
      {icon}
      <div style={{ 
        position: 'absolute' as const, 
        left: 0, 
        top: '25%', 
        bottom: '25%', 
        width: 3, 
        borderRadius: 1.5, 
        background: active ? '#7c3aed' : 'transparent', 
        transition: 'background .15s ease' 
      }} />
    </div>
  );
}

/* ---------- Sidebar (left rail) ---------- */

export default function Sidebar(): JSX.Element {
  const { sidebarVisible, toggleSidebar, setActivePanel, activePanel } = useApp();

  if (!sidebarVisible) return <></>; // hidden entirely when collapsed
  
  /* Left rail with icons - compact design like VS Code / GitHub Desktop */
  
  return (
    <div style={{ 
      width: 48, 
      display: "flex", 
      flexDirection: "column" as const, 
      alignItems: "center", 
      paddingTop: 12, 
      gap: 2 
    }}>
      
      {/* Logo area - click to go home/overview */}
      <div
        title="Home"
        style={{
          width: 40, height: 36, display: "flex", alignItems: "center", justifyContent: "center",
          cursor: "pointer", borderRadius: 8, marginBottom: 12, color: "#a78bfa", fontSize: 20,
        }}
        onClick={() => setActivePanel(null)} 
      >
        <FaBolt />
      </div>

      {/* Module nav items */}
      <NavItem icon={<FaCommentDots size={16} />} label="Chat" active={(activePanel === null || activePanel === "chat")} onClick={() => setActivePanel("chat")} />
      
    </div>
  );
}
