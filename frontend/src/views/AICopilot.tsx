import React, { useState } from 'react';
import { World, CopilotTurnResponse } from '../types';
import { apiClient } from '../api/client';

interface AICopilotProps {
  world: World;
  activeBranchId?: string;
}

interface Message {
  sender: 'user' | 'assistant';
  text: string;
  responsePayload?: CopilotTurnResponse;
}

export const AICopilot: React.FC<AICopilotProps> = ({ world, activeBranchId }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      text: `WorldTwin GenAI Command Layer active for ${world.name}. Every plan is strictly validated against tool allowlists and independently verified against database state before response synthesis. What would you like to simulate or analyze?`
    }
  ]);
  const [inputQuery, setInputQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSend = async (queryText?: string) => {
    const q = queryText || inputQuery;
    if (!q.trim()) return;

    const userMsg: Message = { sender: 'user', text: q };
    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const res = await apiClient.sendCopilotTurn(world.id, q, activeBranchId);
      const assistantMsg: Message = {
        sender: 'assistant',
        text: res.response_text,
        responsePayload: res
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e: any) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `Error executing command loop: ${e.message || 'Unknown error'}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="view-container copilot-chat-layout">
      <div className="chat-messages-container">
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-bubble ${m.sender}`}>
            <div className="bubble-sender mono-tag">
              {m.sender === 'user' ? 'OPERATOR' : 'GENAI COMMAND LAYER (VERIFIED)'}
            </div>
            <div className="bubble-text">{m.text}</div>

            {m.responsePayload && (
              <div className="verification-card">
                <div className="card-header">
                  <span className="mono-label">VERIFIED EXECUTION ARTIFACTS</span>
                  <span className={`status-pill pill-${m.responsePayload.status === 'verified' ? 'green' : 'red'}`}>
                    {m.responsePayload.status.toUpperCase()}
                  </span>
                </div>

                {/* Structured Plan */}
                <div className="plan-section">
                  <div className="sub-label">Structured Plan:</div>
                  <div className="mono-intent">Intent: {m.responsePayload.structured_plan.intent}</div>
                  <div className="tool-chips">
                    {m.responsePayload.structured_plan.tool_calls.map((t, ti) => (
                      <span key={ti} className="tool-badge">
                        🔧 {t.tool_name}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Verification Checks */}
                {m.responsePayload.verification_checks.length > 0 && (
                  <div className="verif-section">
                    <div className="sub-label">Independent DB Verification:</div>
                    {m.responsePayload.verification_checks.map((v, vi) => (
                      <div key={vi} className="verif-row">
                        <span className="icon">{v.verified ? '✅' : '❌'}</span>
                        <span className="detail">{v.details}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Citations */}
                {m.responsePayload.citations.length > 0 && (
                  <div className="citation-section">
                    <div className="sub-label">Knowledge Base Citations:</div>
                    <ul className="cite-list">
                      {m.responsePayload.citations.map((c, ci) => (
                        <li key={ci}>📖 {c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="chat-bubble assistant loading">
            <span>Executing verified tool loop (Intent → Plan → Allowlist → Execution → Verification)...</span>
          </div>
        )}
      </div>

      <div className="chat-input-bar">
        <div className="quick-prompts">
          <button onClick={() => handleSend("What if we close Central Academic Avenue?")}>
            "What if we close Central Academic Avenue?"
          </button>
          <button onClick={() => handleSend("Evaluate interventions to mitigate congestion")}>
            "Evaluate interventions to mitigate congestion"
          </button>
          <button onClick={() => handleSend("Generate a research audit report")}>
            "Generate a research audit report"
          </button>
        </div>
        <div className="input-row">
          <input
            type="text"
            className="chat-text-input"
            value={inputQuery}
            placeholder="Issue a verified natural language digital twin command..."
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button className="btn-primary" onClick={() => handleSend()} disabled={isLoading}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
