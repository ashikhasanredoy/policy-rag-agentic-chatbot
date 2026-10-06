import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Chat from './pages/Chat';
import HelpModal from './components/HelpModal';

export default function App() {
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  return (
    <div className="app-container">
      <Navbar onOpenHelp={() => setIsHelpOpen(true)} />
      <div className="main-content">
        <Chat />
      </div>
      <HelpModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />
    </div>
  );
}
