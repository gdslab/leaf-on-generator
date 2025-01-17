import './ViewMode.css';

import { Dataset, Result } from './MyMap';

export default function ViewMode({
  result,
  setViewMode,
  viewMode,
}: {
  result: Result | null;
  setViewMode: React.Dispatch<React.SetStateAction<'chm' | 'ndhm'>>;
  viewMode: 'chm' | 'ndhm';
}) {
  if (!result || !result?.chm || !result?.ndhm) return;

  return (
    <div className="view-mode">
      <fieldset>
        <legend>Results</legend>
        <h3>Display on map</h3>
        <select
          name="viewMode"
          value={viewMode}
          onChange={(e) => setViewMode(e.target.value as 'chm' | 'ndhm')}
        >
          <option value="chm">CHM</option>
          <option value="ndhm">NDHM</option>
        </select>
        <h3>Download</h3>
        <div
          style={{
            display: 'flex',
            gap: '8px',
          }}
        >
          <a
            href={result.chm.href}
            download="chm.tif"
            aria-label="Download CHM file"
            type="image/tiff"
          >
            CHM (GeoTIFF)
          </a>
          <a
            href={result.ndhm.href}
            download="ndhm.tif"
            aria-label="Download NDHM file"
            type="image/tiff"
          >
            NDHM (GeoTIFF)
          </a>
        </div>
      </fieldset>
    </div>
  );
}
