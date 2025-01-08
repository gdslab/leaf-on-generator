import './DatasetsControl.css';
import { useState } from 'react';

import { Feature } from 'geojson';

import { Dataset, Datasets, Result } from './MyMap';

type DatasetsControlProps = {
  aoi: Feature;
  datasets: Datasets;
  selected3DEP: Dataset | null;
  setSelected3DEP: React.Dispatch<React.SetStateAction<Dataset | null>>;
  setResult: React.Dispatch<React.SetStateAction<Result | null>>;
};

export default function DatasetsControl({
  aoi,
  datasets,
  selected3DEP,
  setSelected3DEP,
  setResult,
}: DatasetsControlProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      const payload = {
        aoi: aoi,
        dataset: selected3DEP,
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
          {/* <h3>NAIP</h3>
          <select>
            {datasets.raster.map(({ id }) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select> */}
        </fieldset>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Running model...' : 'Run model'}
        </button>
      </form>
    </div>
  );
}
