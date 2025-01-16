import 'maplibre-gl/dist/maplibre-gl.css';
import { Feature, FeatureCollection } from 'geojson';
import { useEffect, useRef, useState } from 'react';
import Map, { Layer, MapRef, Source } from 'react-map-gl/maplibre';

import DatasetsControl from './DatasetsControl';
import DrawToolbar from './DrawToolbar';
import ViewMode from './ViewMode';

import { mapboxSatelliteBasemapStyle } from './basemapStyles';

export type Dataset = {
  id: string;
  bbox: [number, number, number, number];
  epsg: number;
  href: string;
};

export type Datasets = {
  point_cloud: Dataset[];
  raster: Dataset[];
};

export type Result = {
  chm: {
    href: string;
    rescale: string;
  };
  ndhm: {
    href: string;
    rescale: string;
  };
  session_id: string;
};

export default function MyMap() {
  const [aoi, setAoi] = useState<Feature | null>(null);
  const [datasets, setDatasets] = useState<Datasets | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [selected3dep, setSelected3dep] = useState<Dataset | null>(null);
  const [viewMode, setViewMode] = useState<'chm' | 'ndhm'>('chm');

  const mapRef = useRef<MapRef | null>(null);

  useEffect(() => {
    if (mapRef.current && selected3dep) {
      const map = mapRef.current.getMap();

      map.fitBounds(selected3dep.bbox, {
        padding: 20,
        duration: 1000,
      });
    }
  }, [selected3dep]);

  const getBboxGeojson = (
    bbox: [number, number, number, number]
  ): FeatureCollection => ({
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [bbox[0], bbox[1]],
              [bbox[2], bbox[1]],
              [bbox[2], bbox[3]],
              [bbox[0], bbox[3]],
              [bbox[0], bbox[1]],
            ],
          ],
        },
        properties: {},
      },
    ],
  });

  return (
    <Map
      ref={mapRef}
      initialViewState={{
        longitude: -86.921195,
        latitude: 40.423705,
        zoom: 14,
      }}
      style={{ width: '100%', height: '100%' }}
      mapStyle={mapboxSatelliteBasemapStyle}
    >
      {aoi && datasets && (
        <DatasetsControl
          aoi={aoi}
          datasets={datasets}
          selected3DEP={selected3dep}
          setSelected3DEP={setSelected3dep}
          setResult={setResult}
        />
      )}
      {selected3dep && !result && (
        <Source
          id="bbox-source"
          type="geojson"
          data={getBboxGeojson(selected3dep.bbox)}
        >
          <Layer
            id="bbox-layer"
            type="fill"
            paint={{ 'fill-color': '#888888', 'fill-opacity': 0.5 }}
          />
          <Layer
            id="bbox-border"
            type="line"
            paint={{
              'line-color': '#000000',
              'line-width': 2,
            }}
          />
        </Source>
      )}
      {result && (
        <Source
          key={viewMode}
          id={`${viewMode}-source`}
          type="raster"
          tiles={[
            `/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@2x?url=${result[viewMode].href}&rescale=${result[viewMode].rescale}`,
          ]}
          maxzoom={24}
          minzoom={0}
          tileSize={512}
        >
          <Layer id={`${viewMode}-layer`} type="raster" source={result.session_id} />
        </Source>
      )}
      <DrawToolbar setAoi={setAoi} setDatasets={setDatasets} />
      {result && <ViewMode setViewMode={setViewMode} viewMode={viewMode} />}
    </Map>
  );
}
