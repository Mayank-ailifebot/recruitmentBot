import React, { useState } from 'react';
import HiringManagerView from './components/HiringManagerView';
import CandidatePortalView from './components/CandidatePortalView';
import { Briefcase, User } from 'lucide-react';

function App() {
  const [view, setView] = useState<'manager' | 'candidate'>('manager');

  return (
    <div className="min-h-screen bg-black text-gray-200 font-sans selection:bg-purple-500/30">
      {/* Top Navigation */}
      <nav className="bg-gray-950 border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-purple-600 rounded flex items-center justify-center font-bold text-white shadow-lg shadow-purple-500/20">
                AI
              </div>
              <span className="text-xl font-bold text-white tracking-tight">RecruitBot<span className="text-purple-500">.</span></span>
            </div>
            
            {/* View Toggle */}
            <div className="flex bg-gray-900 p-1 rounded-lg border border-gray-800">
              <button 
                onClick={() => setView('manager')}
                className={`flex items-center px-4 py-1.5 rounded-md text-sm font-medium transition-all ${view === 'manager' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
              >
                <Briefcase className="w-4 h-4 mr-2" /> Hiring Manager
              </button>
              <button 
                onClick={() => setView('candidate')}
                className={`flex items-center px-4 py-1.5 rounded-md text-sm font-medium transition-all ${view === 'candidate' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
              >
                <User className="w-4 h-4 mr-2" /> Candidate Portal
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
         {view === 'manager' ? <HiringManagerView /> : <CandidatePortalView />}
      </main>
    </div>
  );
}

export default App;
