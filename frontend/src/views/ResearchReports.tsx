import React, { useState, useEffect } from 'react';
import { World, ResearchReport } from '../types';
import { apiClient } from '../api/client';

interface ResearchReportsProps {
  world: World;
  activeBranchId?: string;
}

export const ResearchReports: React.FC<ResearchReportsProps> = ({ world, activeBranchId }) => {
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  useEffect(() => {
    loadReports();
  }, [world.id]);

  const loadReports = async () => {
    try {
      const list = await apiClient.listReports(world.id);
      setReports(list);
      if (list.length > 0 && !selectedReport) {
        const full = await apiClient.getReport(list[0].id);
        setSelectedReport(full);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerate = async () => {
    if (!activeBranchId) {
      alert("Please select an active branch first.");
      return;
    }
    setIsGenerating(true);
    try {
      const rep = await apiClient.generateReport(world.id, activeBranchId);
      setReports(prev => [rep, ...prev]);
      setSelectedReport(rep);
    } catch (e: any) {
      alert(e.message || "Report generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectReport = async (repId: string) => {
    try {
      const full = await apiClient.getReport(repId);
      setSelectedReport(full);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="view-container reports-layout">
      <div className="reports-sidebar-card">
        <div className="reports-header">
          <h3>Audits & Reports</h3>
          <button className="btn-primary" onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? 'Compiling...' : '+ New Report'}
          </button>
        </div>

        <div className="reports-scroll-list">
          {reports.map(r => (
            <div
              key={r.id}
              className={`report-item-card ${selectedReport?.id === r.id ? 'active' : ''}`}
              onClick={() => handleSelectReport(r.id)}
            >
              <h4 className="report-card-title">{r.title}</h4>
              <div className="report-card-summary">{r.summary}</div>
              <span className="mono-date">{r.created_at || 'Just now'}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="report-viewer-card">
        {selectedReport ? (
          <div className="markdown-doc-view">
            <pre className="report-markdown-pre">{selectedReport.content}</pre>
          </div>
        ) : (
          <div className="placeholder-box">Select or generate a report to view full markdown content.</div>
        )}
      </div>
    </div>
  );
};
