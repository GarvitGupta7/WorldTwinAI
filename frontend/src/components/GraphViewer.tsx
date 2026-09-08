import React, { useState } from 'react';
import { Entity, Relationship } from '../types';

interface GraphViewerProps {
  entities: Entity[];
  relationships: Relationship[];
  onSelectEntity: (entity: Entity | null) => void;
  selectedEntityId?: string;
}

export const GraphViewer: React.FC<GraphViewerProps> = ({
  entities,
  relationships,
  onSelectEntity,
  selectedEntityId
}) => {
  const [zoom, setZoom] = useState<number>(1.0);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const roads = entities.filter(e => e.entity_type === 'road' || e.entity_type === 'corridor');
  const buildings = entities.filter(e => e.entity_type === 'building' || e.entity_type === 'ward' || e.entity_type === 'terminal');
  const dynamicEntities = entities.filter(e => ['bus', 'student', 'staff', 'ambulance', 'patient'].includes(e.entity_type));

  const getEntityColor = (type: string, state: any) => {
    if (state?.blocked) return '#ef4444';
    switch (type) {
      case 'building':
      case 'ward':
      case 'terminal':
        return '#3b82f6';
      case 'road':
        const ci = state?.congestion_index || 0.2;
        return ci > 0.7 ? '#ef4444' : ci > 0.45 ? '#f59e0b' : '#10b981';
      case 'bus':
      case 'ambulance':
        return '#f97316';
      case 'student':
      case 'patient':
        return '#06b6d4';
      default:
        return '#8b5cf6';
    }
  };

  return (
    <div className="canvas-wrapper">
      <div className="canvas-toolbar">
        <span className="mono-label">SPATIAL TOPOLOGY & TWIN MAP</span>
        <div className="zoom-controls">
          <button onClick={() => setZoom(z => Math.max(0.6, z - 0.2))}>-</button>
          <span>{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom(z => Math.min(2.5, z + 0.2))}>+</button>
          <button onClick={() => { setZoom(1.0); setPan({ x: 0, y: 0 }); }}>Reset</button>
        </div>
      </div>

      <svg
        className="twin-svg-canvas"
        viewBox="0 0 1000 1000"
        style={{ transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)` }}
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1f2937" strokeWidth="0.8" />
          </pattern>
        </defs>
        <rect width="1000" height="1000" fill="url(#grid)" />

        {/* Relationship lines */}
        {relationships.map((rel) => {
          const src = entities.find(e => e.id === rel.source_entity_id);
          const tgt = entities.find(e => e.id === rel.target_entity_id);
          if (!src || !tgt) return null;
          return (
            <line
              key={rel.id}
              x1={src.position.x}
              y1={src.position.y}
              x2={tgt.position.x}
              y2={tgt.position.y}
              stroke="#374151"
              strokeWidth="1.2"
              strokeDasharray="4 3"
            />
          );
        })}

        {/* Roads / Corridors */}
        {roads.map(r => {
          const color = getEntityColor(r.entity_type, r.state);
          const isSelected = r.id === selectedEntityId;
          return (
            <g key={r.id} onClick={() => onSelectEntity(r)} className="map-node-interactive">
              <circle
                cx={r.position.x}
                cy={r.position.y}
                r={isSelected ? 16 : 12}
                fill={color}
                opacity={0.85}
                stroke={isSelected ? '#ffffff' : '#111827'}
                strokeWidth={isSelected ? 3 : 1.5}
              />
              <text x={r.position.x + 16} y={r.position.y + 4} fill="#9ca3af" fontSize="11" fontFamily="monospace">
                {r.name}
              </text>
            </g>
          );
        })}

        {/* Buildings / Wards */}
        {buildings.map(b => {
          const isSelected = b.id === selectedEntityId;
          return (
            <g key={b.id} onClick={() => onSelectEntity(b)} className="map-node-interactive">
              <rect
                x={b.position.x - 30}
                y={b.position.y - 20}
                width={60}
                height={40}
                rx={6}
                fill="#1e3a8a"
                stroke={isSelected ? '#60a5fa' : '#3b82f6'}
                strokeWidth={isSelected ? 3 : 1.5}
                opacity={0.9}
              />
              <text x={b.position.x} y={b.position.y + 4} fill="#e5e7eb" fontSize="10" fontWeight="bold" textAnchor="middle">
                {b.name.length > 12 ? b.name.substring(0, 10) + '..' : b.name}
              </text>
            </g>
          );
        })}

        {/* Dynamic Entities (Buses, Students, Ambulances) */}
        {dynamicEntities.map(e => {
          const isSelected = e.id === selectedEntityId;
          const color = getEntityColor(e.entity_type, e.state);
          return (
            <g key={e.id} onClick={() => onSelectEntity(e)} className="map-node-interactive">
              <circle
                cx={e.position.x}
                cy={e.position.y}
                r={isSelected ? 9 : 5}
                fill={color}
                stroke="#111827"
                strokeWidth="1"
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
};
