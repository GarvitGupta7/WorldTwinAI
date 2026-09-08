import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client.js';



export const KnowledgeGraph = ({ world, relationships }) => {
  const [searchQuery, setSearchQuery] = useState('emergency');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    handleSearch();
  }, [world.id]);

  const handleSearch = async () => {
    setIsSearching(true);
    try {
      const docs = await apiClient.searchKnowledge(world.id, searchQuery);
      setSearchResults(docs);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="view-container knowledge-layout">
      <div className="knowledge-search-card">
        <h3>Domain Knowledge Base (RAG)</h3>
        <p className="subtext">Operational procedures and safety regulations for {world.name}.</p>

        <div className="search-bar">
          <input
            type="text"
            className="text-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search operational documentation..."
          />
          <button className="btn-primary" onClick={handleSearch} disabled={isSearching}>
            Search
          </button>
        </div>

        <div className="docs-list">
          {searchResults.map((d, i) => (
            <div key={i} className="doc-item">
              <div className="doc-title-row">
                <h4>{d.title}</h4>
                <span className="doc-score">Score))}
        </div>
      </div>

      <div className="topology-relations-card">
        <h3>Declared Relationship Graph</h3>
        <p className="subtext">Graph topology schema connecting entities in this world.</p>
        <div className="rel-list">
          {world.schema_definition?.declared_relationship_types?.map((r, idx) => (
            <div key={idx} className="rel-type-item">
              <span className="mono bold">{r.source_entity_type}</span>
              <span className="rel-arrow">──[{r.relationship_type}]──▶</span>
              <span className="mono bold">{r.target_entity_type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
