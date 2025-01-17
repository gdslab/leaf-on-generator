import './DatasetsControl.css';
import { Feature } from 'geojson';
import { useState } from 'react';

import { Dataset, Datasets, Model, Result } from './MyMap';
import ViewMode from './ViewMode';

type DatasetsControlProps = {
  aoi: Feature;
  datasets: Datasets;
  result: Result | null;
  setDatasets: React.Dispatch<React.SetStateAction<Datasets | null>>;
  selected3DEP: Dataset | null;
  selectedModel: Model;
  selectedNaip: Dataset | null;
  setSelected3DEP: React.Dispatch<React.SetStateAction<Dataset | null>>;
  setSelectedModel: React.Dispatch<React.SetStateAction<Model>>;
  setSelectedNaip: React.Dispatch<React.SetStateAction<Dataset | null>>;
  setResult: React.Dispatch<React.SetStateAction<Result | null>>;
  viewMode: 'chm' | 'ndhm';
  setViewMode: React.Dispatch<React.SetStateAction<'ndhm' | 'chm'>>;
};

export default function DatasetsControl({
  aoi,
  datasets,
  result,
  setDatasets,
  selected3DEP,
  selectedModel,
  selectedNaip,
  setSelected3DEP,
  setSelectedModel,
  setSelectedNaip,
  setResult,
  viewMode,
  setViewMode,
}: DatasetsControlProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleReset = () => {
    setResult(null);
    setSelected3DEP(null);
    setSelectedNaip(null);
    setDatasets(null);
    setViewMode('chm');
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      const payload = {
        aoi: aoi,
        lidar: selected3DEP,
        naip: selectedNaip,
        model: selectedModel,
      };
      const response = await fetch('/api/model', {
        method: 'post',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      setResult(result);
      setIsSubmitting(false);
    } catch (err) {
      console.error('Error:', err);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="control">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
      >
        <fieldset>
          <legend>Select Dataset</legend>
          <label htmlFor="model">Select model:</label>
          <input
            type="radio"
            name="model"
            value="lidar"
            checked={selectedModel == 'lidar'}
            onChange={(e) => {
              setSelectedModel(e.target.value as Model);
              setSelectedNaip(null);
            }}
          />
          LiDAR
          <input
            type="radio"
            name="model"
            value="both"
            checked={selectedModel == 'both'}
            onChange={(e) => setSelectedModel(e.target.value as Model)}
          />
          LiDAR + Spectral
          <h3>3DEP</h3>
          <select
            onChange={(e) => {
              const selected = datasets.point_cloud.find(
                ({ id }) => id === e.target.value
              );
              if (selected) {
                setSelected3DEP(selected);
              }
            }}
            value={selected3DEP?.id || ''}
          >
            <option value="">Select 3DEP dataset</option>
            {datasets.point_cloud.map(({ id }) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          {selectedModel === 'both' && (
            <div>
              <h3>NAIP</h3>
              <select
                onChange={(e) => {
                  const selected = datasets.raster.find(
                    ({ id }) => id === e.target.value
                  );
                  if (selected) {
                    setSelectedNaip(selected);
                  }
                }}
                value={selectedNaip?.id || ''}
              >
                <option value="">Select NAIP dataset</option>
                {datasets.raster.map(({ id }) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </div>
          )}
        </fieldset>
        <button className="submit-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Running model...' : 'Run model'}
        </button>
      </form>
      {result && result?.[viewMode] && (
        <ViewMode result={result} viewMode={viewMode} setViewMode={setViewMode} />
      )}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', marginTop: 15 }}>
          <button
            className="reset-button"
            type="submit"
            disabled={isSubmitting}
            onClick={handleReset}
          >
            Reset
          </button>
        </div>
      )}
    </div>
  );
}
