import React, { useState } from 'react';
import { UploadCloud, MessageSquare, ShieldCheck, UserCircle, Send } from 'lucide-react';

export default function CandidatePortalView() {
  const [step, setStep] = useState(0); // 0: Upload, 1: Parsing, 2: Chat
  const [chatLog, setChatLog] = useState<{role: 'ai' | 'user', text: string}[]>([
    { role: 'ai', text: "Hi! I'm the AI Recruiter. I've reviewed your resume and noticed your strong background in sales. Could you tell me about the most difficult conflict you resolved with a client?" }
  ]);
  const [inputText, setInputText] = useState('');

  const handleUpload = () => {
    setStep(1);
    setTimeout(() => {
      setStep(2);
    }, 3000);
  };

  const handleSend = () => {
    if (!inputText) return;
    setChatLog([...chatLog, { role: 'user', text: inputText }]);
    setInputText('');
    
    // Fake AI response
    setTimeout(() => {
      setChatLog(prev => [...prev, { role: 'ai', text: "That's a very structured approach to conflict resolution. How do you usually handle situations where you fall short of your quarterly targets?" }]);
    }, 1500);
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-8 text-gray-200">
       <div className="text-center space-y-2">
         <h2 className="text-3xl font-bold text-white">Candidate Portal</h2>
         <p className="text-gray-400">Apply for: Insurance Sales Lead</p>
       </div>

       {step === 0 && (
         <div 
           className="border-2 border-dashed border-gray-700 hover:border-purple-500 bg-gray-900/50 rounded-2xl p-12 text-center cursor-pointer transition-all group"
           onClick={handleUpload}
         >
           <UploadCloud className="w-16 h-16 text-gray-500 group-hover:text-purple-400 mx-auto mb-4 transition-colors" />
           <h3 className="text-xl font-semibold text-white mb-2">Upload Resume</h3>
           <p className="text-gray-400 text-sm">PDF, DOCX, or Image (Max 5MB)</p>
           <p className="text-xs text-purple-500 mt-4 font-mono uppercase tracking-wider">Click anywhere to simulate upload</p>
         </div>
       )}

       {step === 1 && (
         <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-6 shadow-2xl">
            <div className="animate-spin w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto"></div>
            <h3 className="text-xl font-bold text-white">Extracting Profile Details...</h3>
            <div className="space-y-3 text-sm font-mono text-gray-400 text-left max-w-sm mx-auto">
              <div className="flex justify-between items-center"><span className="animate-pulse">Reading Document...</span> <ShieldCheck className="w-4 h-4 text-green-500"/></div>
              <div className="flex justify-between items-center"><span className="animate-pulse" style={{animationDelay: '0.5s'}}>Parsing Skills & Tenure...</span> <ShieldCheck className="w-4 h-4 text-green-500"/></div>
              <div className="flex justify-between items-center"><span className="animate-pulse" style={{animationDelay: '1s'}}>Running Anomaly Checks...</span> <ShieldCheck className="w-4 h-4 text-green-500"/></div>
            </div>
         </div>
       )}

       {step === 2 && (
         <div className="bg-gray-900 border border-gray-800 rounded-xl shadow-2xl flex flex-col h-[500px]">
           <div className="p-4 border-b border-gray-800 flex items-center bg-gray-950 rounded-t-xl">
              <div className="w-10 h-10 rounded-full bg-purple-900/50 border border-purple-500 flex items-center justify-center mr-3">
                 <Bot className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h3 className="text-white font-semibold">AI Interviewer</h3>
                <p className="text-xs text-green-400 flex items-center"><span className="w-2 h-2 rounded-full bg-green-500 mr-1 animate-pulse"></span> Active Screening</p>
              </div>
           </div>

           <div className="flex-1 overflow-y-auto p-4 space-y-4">
             {chatLog.map((msg, idx) => (
               <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-purple-600 text-white rounded-br-none' : 'bg-gray-800 text-gray-200 border border-gray-700 rounded-bl-none'}`}>
                    {msg.text}
                  </div>
               </div>
             ))}
           </div>

           <div className="p-4 border-t border-gray-800 bg-gray-950 rounded-b-xl flex gap-2">
             <input 
               type="text"
               value={inputText}
               onChange={e => setInputText(e.target.value)}
               onKeyDown={e => e.key === 'Enter' && handleSend()}
               placeholder="Type your response..."
               className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
             />
             <button onClick={handleSend} className="bg-purple-600 hover:bg-purple-700 text-white p-2 rounded-lg transition-colors flex items-center justify-center w-12">
                <Send className="w-5 h-5" />
             </button>
           </div>
         </div>
       )}
    </div>
  );
}

// Quick inline stub for Bot icon since it wasn't imported in the list initially but used
import { Bot } from 'lucide-react';
