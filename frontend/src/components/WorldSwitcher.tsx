import React, { useState } from 'react';
import { World } from '../types';

interface WorldSwitcherProps {
  worlds: World[];
  activeWorldId: string;
  onSelectWorld: (worldId: string) => void;
  onOpenCreateModal: () => void;
}

export const WorldSwitcher: React.FC<WorldSwitcherProps> = ({
  worlds,
  activeWorldId,
  onSelectWorld,
  onOpenCreateModal
}) => {
  const activeWorld = worlds.find(w => w.id === activeWorldId);

  return (
    <div className="world-switcher-bar">
      <div className="switcher-left">
        <span className="mono-tag">CURRENT TWIN WORLD</span>
        <select
          className="world-select"
          value={activeWorldId}
          onChange={(e) => onSelectWorld(e.target.value)}
        >
          {worlds.map(w => (
            <option key={w.id} value={w.id}>
              {w.name} ({w.world_type.toUpperCase()})
            </option>
          ))}
        </select>
        {activeWorld && (
          <span className="world-meta">
            Types: {activeWorld.schema_definition?.declared_entity_types?.join(', ') || 'N/A'}
          </span>
        )}
      </div>

      <div className="switcher-right">
        <button className="btn-secondary" onClick={onOpenCreateModal}>
          + Propose New World (GenAI)
        </button>
      </div>
    </div>
  );
};
