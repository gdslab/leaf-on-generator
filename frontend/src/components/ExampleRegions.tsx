import { FC } from 'react';

export type Region = 'kansas' | 'manhattan' | 'purdue';

export const regionCoordinates: Record<Region, [number, number]> = {
  kansas: [-95.2353, 38.9717], // Lawrence, Kansas coordinates
  manhattan: [-73.935242, 40.73061],
  purdue: [-86.921195, 40.423705],
};

interface ExampleRegionsProps {
  onRegionSelect: (region: Region) => void;
}

const ExampleRegions: FC<ExampleRegionsProps> = ({ onRegionSelect }) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: '10px',
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        padding: '12px 24px',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        zIndex: 1,
        color: 'black',
        fontFamily: 'Arial, sans-serif',
        maxWidth: '400px',
      }}
    >
      <div
        style={{
          marginBottom: '8px',
          fontWeight: 'bold',
          color: 'black',
          fontSize: '16px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        Example Areas
      </div>
      <div
        style={{
          display: 'flex',
          gap: '20px',
          color: 'black',
          fontSize: '14px',
          marginBottom: '12px',
        }}
      >
        <label
          style={{
            color: 'black',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <input
            type="radio"
            name="region"
            value="kansas"
            defaultChecked
            onChange={(e) => onRegionSelect(e.target.value as Region)}
            style={{ cursor: 'pointer' }}
          />
          Lawrence
        </label>
        <label
          style={{
            color: 'black',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <input
            type="radio"
            name="region"
            value="manhattan"
            onChange={(e) => onRegionSelect(e.target.value as Region)}
            style={{ cursor: 'pointer' }}
          />
          Manhattan
        </label>
        <label
          style={{
            color: 'black',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
          }}
        >
          <input
            type="radio"
            name="region"
            value="purdue"
            onChange={(e) => onRegionSelect(e.target.value as Region)}
            style={{ cursor: 'pointer' }}
          />
          Purdue
        </label>
      </div>
      <div
        style={{
          fontSize: '13px',
          color: '#333',
          borderTop: '1px solid #ddd',
          paddingTop: '12px',
          lineHeight: '1.4',
        }}
      >
        <p style={{ margin: '0 0 8px 0' }}>
          <strong>Getting Started:</strong> Use the drawing toolbar on the left
          to draw a polygon around your area of interest. The map will
          automatically zoom to your selection.
        </p>
      </div>
    </div>
  );
};

export default ExampleRegions;
