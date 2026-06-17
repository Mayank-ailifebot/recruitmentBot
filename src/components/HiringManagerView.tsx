import React, { useState, useEffect } from 'react';
import { Bot, FileText, Search, Play, Users, CheckCircle, Clock } from 'lucide-react';

export default function HiringManagerView() {
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [showDashboard, setShowDashboard] = useState(false);

  const simulateWorkflow = async () => {
    setIsProcessing(true);
    setLogs([]);
    
    const steps = [
      "Analyzing CRM/Sales dashboard for top performers...",
      "Found 3 Success Vectors: Pharma background, Tenure > 2 yrs, High outgoing activity.",
      "Generating inclusive job description...",
      "Preparing multi-channel campaign...",
      "Job Campaign Live."
    ];

    for (let i = 0; i < steps.length; i++) {
      await new Promise(r => setTimeout(r, 1200));
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${steps[i]}`]);
    }

    setTimeout(() => {
      setIsProcessing(false);
      setShowDashboard(true);
    }, 1000);
  };

  return (
    <div className="p-6 space-y-6 text-gray-200">
      {!showDashboard ? (
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl">
            <h2 className="text-2xl font-bold mb-4 flex items-center text-white"><Search className="mr-3 text-purple-500" /> Start New Requisition</h2>
            <p className="text-gray-400 mb-6">Describe the role, and the AI Orchestrator will handle sourcing, screening, and matching.</p>
            <div className="space-y-4">
              <textarea 
                className="w-full bg-gray-950 border border-gray-800 rounded-lg p-4 text-white focus:outline-none focus:border-purple-500 transition-colors h-32"
                placeholder="e.g., Need 3 Insurance Sales Leads in Delhi. Fluent in Hindi. Must have 3+ years experience..."
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
              />
              <button 
                onClick={simulateWorkflow}
                disabled={isProcessing || !prompt}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium py-3 px-6 rounded-lg transition-all flex items-center justify-center w-full"
              >
                {isProcessing ? <span className="animate-pulse">Processing...</span> : <><Play className="w-4 h-4 mr-2" /> Generate Job Campaign</>}
              </button>
            </div>
          </div>

          {isProcessing && (
            <div className="bg-black border border-gray-800 rounded-xl p-6 font-mono text-sm text-green-400 h-64 overflow-y-auto shadow-inner">
              <div className="flex items-center mb-4 text-purple-400 border-b border-gray-800 pb-2">
                <Bot className="w-5 h-5 mr-2 animate-bounce" /> AI Orchestrator Live Feed
              </div>
              {logs.map((log, i) => (
                <div key={i} className="mb-2 animate-fade-in-up">{log}</div>
              ))}
              <div className="animate-pulse mt-2">_</div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
           <div className="flex justify-between items-end border-b border-gray-800 pb-4">
             <div>
               <h2 className="text-3xl font-bold text-white">Insurance Sales Lead</h2>
               <p className="text-gray-400 mt-1">Delhi NCR • Full-Time • Active Campaign</p>
             </div>
             <div className="flex space-x-4">
                <div className="flex items-center text-sm bg-gray-900 px-3 py-1 rounded border border-gray-800"><CheckCircle className="w-4 h-4 text-green-500 mr-2"/> LinkedIn Live</div>
                <div className="flex items-center text-sm bg-gray-900 px-3 py-1 rounded border border-gray-800"><CheckCircle className="w-4 h-4 text-green-500 mr-2"/> Naukri Live</div>
             </div>
           </div>

           {/* Pipeline UI Mock */}
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
             <div className="col-span-2 space-y-4">
                <h3 className="text-xl font-semibold flex items-center"><Users className="mr-2 text-purple-500" /> Active Candidates</h3>
                
                {/* Candidate Card 1 */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 hover:border-purple-500 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="text-lg font-bold text-white">Rahul Sharma</h4>
                      <div className="text-sm text-gray-400 mt-1 flex space-x-2">
                         <span className="bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded text-xs border border-blue-800">Recycled Talent</span>
                         <span className="bg-green-900/50 text-green-300 px-2 py-0.5 rounded text-xs border border-green-800">High Performer Match</span>
                      </div>
                    </div>
                    <div className="text-right">
                       <div className="text-2xl font-bold text-green-400">92%</div>
                       <div className="text-xs text-gray-500 uppercase tracking-wide">Overall Fit</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                     <div>
                       <div className="text-gray-500 mb-1">Hard Skills</div>
                       <div className="w-full bg-gray-800 rounded-full h-1.5"><div className="bg-purple-500 h-1.5 rounded-full" style={{width: '90%'}}></div></div>
                     </div>
                     <div>
                       <div className="text-gray-500 mb-1">Experience</div>
                       <div className="w-full bg-gray-800 rounded-full h-1.5"><div className="bg-purple-500 h-1.5 rounded-full" style={{width: '95%'}}></div></div>
                     </div>
                     <div>
                       <div className="text-gray-500 mb-1">Behavioral</div>
                       <div className="w-full bg-gray-800 rounded-full h-1.5"><div className="bg-purple-500 h-1.5 rounded-full" style={{width: '88%'}}></div></div>
                     </div>
                  </div>
                  <div className="bg-gray-950 p-3 rounded text-sm text-gray-300 border border-gray-800">
                    <span className="text-purple-400 font-semibold">Snapshot:</span> "Assertive communicator with strong adjacent industry experience (Pharma). Displayed high resilience in AI interview."
                  </div>
                </div>

                {/* Candidate Card 2 */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="text-lg font-bold text-white">Priya Patel</h4>
                       <div className="text-sm text-gray-400 mt-1 flex space-x-2">
                         <span className="bg-purple-900/50 text-purple-300 px-2 py-0.5 rounded text-xs border border-purple-800">New Applicant</span>
                      </div>
                    </div>
                    <div className="text-right">
                       <div className="text-2xl font-bold text-yellow-400">76%</div>
                       <div className="text-xs text-gray-500 uppercase tracking-wide">Overall Fit</div>
                    </div>
                  </div>
                  <div className="bg-gray-950 p-3 rounded flex items-center justify-center text-sm text-gray-500 border border-gray-800 border-dashed">
                    <Clock className="w-4 h-4 mr-2" /> AI Interview Pending
                  </div>
                </div>
             </div>

             <div className="space-y-4">
               <h3 className="text-xl font-semibold flex items-center"><FileText className="mr-2 text-purple-500" /> Pipeline Stats</h3>
               <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-4">
                 <div className="flex justify-between items-center border-b border-gray-800 pb-2">
                   <span className="text-gray-400">Total Applicants</span>
                   <span className="text-xl font-bold text-white">12</span>
                 </div>
                 <div className="flex justify-between items-center border-b border-gray-800 pb-2">
                   <span className="text-gray-400">AI Screened</span>
                   <span className="text-xl font-bold text-white">4</span>
                 </div>
                 <div className="flex justify-between items-center pb-2">
                   <span className="text-gray-400">Shortlisted (80%+)</span>
                   <span className="text-xl font-bold text-green-400">2</span>
                 </div>
               </div>
             </div>
           </div>
        </div>
      )}
    </div>
  );
}
