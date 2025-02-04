import './ViewMode.css';

import { Result } from './MyMap';

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
        <div
          style={{
            display: 'flex',
            gap: '8px',
          }}
        >
          <div>
            <input
              type="radio"
              id="chm"
              name="viewMode"
              value="chm"
              checked={viewMode === 'chm'}
              onChange={(e) => setViewMode(e.target.value as 'chm')}
            />
            <label htmlFor="chm">Generated CHM</label>
          </div>
          <div>
            <input
              type="radio"
              id="ndhm"
              name="viewMode"
              value="ndhm"
              checked={viewMode === 'ndhm'}
              onChange={(e) => setViewMode(e.target.value as 'ndhm')}
            />
            <label htmlFor="ndhm">Original CHM</label>
          </div>
          {result?.naip && (
            <div>
              <input
                type="radio"
                id="naip"
                name="viewMode"
                value="naip"
                checked={viewMode === 'naip'}
                onChange={(e) => setViewMode(e.target.value as 'naip')}
              />
              <label htmlFor="naip">NAIP</label>
            </div>
          )}
        </div>

        <h3>Download</h3>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <a
            href={result.chm.href}
            download="generated-chm.tif"
            aria-label="Download Generated CHM file"
            type="image/tiff"
          >
            {`Generated CHM (GeoTIFF, ${(
              result.chm.file_size /
              (1024 * 1024)
            ).toFixed(2)} MB)`}
          </a>
          <a
            href={result.ndhm.href}
            download="original-chm.tif"
            aria-label="Download Original CHM file"
            type="image/tiff"
          >
            {`Original CHM (GeoTIFF, ${(
              result.ndhm.file_size /
              (1024 * 1024)
            ).toFixed(2)} MB)`}
          </a>
          {result.naip && (
            <a
              href={result.naip.href}
              download="naip.tif"
              aria-label="Download NAIP file"
              type="image/tiff"
            >
              {`NAIP (GeoTIFF, ${(
                result.naip.file_size /
                (1024 * 1024)
              ).toFixed(2)} MB)`}
            </a>
          )}
        </div>
      </fieldset>
    </div>
  );
}
