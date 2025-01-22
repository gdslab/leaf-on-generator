import './ViewMode.css';

import { Dataset, Result } from './MyMap';

export default function ViewMode({
  result,
  setViewMode,
  viewMode,
}: {
  result: Result | null;
  setViewMode: React.Dispatch<React.SetStateAction<'chm' | 'ndhm' | 'naip'>>;
  viewMode: 'chm' | 'ndhm' | 'naip';
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
          onChange={(e) =>
            setViewMode(e.target.value as 'chm' | 'ndhm' | 'naip')
          }
        >
          <option value="chm">CHM</option>
          <option value="ndhm">NDHM</option>
          {result.naip && <option value="naip">NAIP</option>}
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
          {result.naip && (
            <a
              href={result.naip.href}
              download="naip.tif"
              aria-label="Download NAIP file"
              type="image/tiff"
            >
              NAIP (GeoTIFF)
            </a>
          )}
        </div>
      </fieldset>
    </div>
  );
}
