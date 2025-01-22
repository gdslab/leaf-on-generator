import 'maplibre-gl/dist/maplibre-gl.css';
import { Feature } from 'geojson';
import { useEffect, useRef, useState } from 'react';
import Map, { Layer, MapRef, Source } from 'react-map-gl/maplibre';
import * as turf from '@turf/turf';

import DatasetsControl from './DatasetsControl';
import DrawToolbar from './DrawToolbar';

import { mapboxSatelliteBasemapStyle } from './basemapStyles';
import { getBboxGeojson } from './utils';

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

export interface FeatureWithId extends Feature {
  id: string;
}

export type Model = 'lidar' | 'both';

export type Result = {
  chm: {
    href: string;
    rescale: string;
  };
  ndhm: {
    href: string;
    rescale: string;
  };
  naip?: {
    href: string;
    rescale: string;
  };
  session_id: string;
};

export default function MyMap() {
  const [aoi, setAoi] = useState<FeatureWithId | null>(null);
  const [datasets, setDatasets] = useState<Datasets | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [selected3dep, setSelected3dep] = useState<Dataset | null>(null);
  const [selectedModel, setSelectedModel] = useState<Model>('lidar');
  const [selectedNaip, setSelectedNaip] = useState<Dataset | null>(null);
  const [viewMode, setViewMode] = useState<'chm' | 'ndhm' | 'naip'>('chm');
  const [datasetsIntersection, setDatasetsIntersection] =
    useState<Feature | null>(null);

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

  useEffect(() => {
    if (mapRef.current && aoi && result) {
      const map = mapRef.current.getMap();
      const bbox = turf.bbox(aoi);

      if (bbox.length === 4) {
        map.fitBounds(bbox, {
          padding: 20,
          duration: 1000,
        });
      }
    }
  }, [result]);

  useEffect(() => {
    if (selected3dep && selectedNaip) {
      const polygon1 = turf.bboxPolygon(selected3dep.bbox);
      const polygon2 = turf.bboxPolygon(selectedNaip.bbox);
      const intersection = turf.intersect(
        turf.featureCollection([polygon1, polygon2])
      );
      setDatasetsIntersection(intersection);
      if (mapRef.current) {
        const map = mapRef.current.getMap();
        if (intersection) {
          const bbox = turf.bbox(intersection);
          if (bbox.length === 4) {
            map.fitBounds(bbox, {
              padding: 20,
              duration: 1000,
            });
          }
        }
      }
    }
  }, [selected3dep, selectedNaip]);

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
          result={result}
          setDatasets={setDatasets}
          selected3DEP={selected3dep}
          selectedModel={selectedModel}
          selectedNaip={selectedNaip}
          setSelected3DEP={setSelected3dep}
          setSelectedModel={setSelectedModel}
          setSelectedNaip={setSelectedNaip}
          setResult={setResult}
          setViewMode={setViewMode}
          viewMode={viewMode}
        />
      )}
      {selected3dep && !datasetsIntersection && !result && (
        <Source
          id="bbox-3dep-source"
          type="geojson"
          data={getBboxGeojson(selected3dep.bbox)}
        >
          <Layer
            id="bbox-3dep-layer"
            type="fill"
            paint={{ 'fill-color': '#888888', 'fill-opacity': 0.5 }}
          />
          <Layer
            id="bbox-3dep-border"
            type="line"
            paint={{
              'line-color': '#000000',
              'line-width': 2,
            }}
          />
        </Source>
      )}
      {selectedNaip && !datasetsIntersection && !result && (
        <Source
          id="bbox-naip-source"
          type="geojson"
          data={getBboxGeojson(selectedNaip.bbox)}
        >
          <Layer
            id="bbox-naip-layer"
            type="fill"
            paint={{ 'fill-color': '#a3e635', 'fill-opacity': 0.5 }}
          />
          <Layer
            id="bbox-naip-border"
            type="line"
            paint={{
              'line-color': '#000000',
              'line-width': 2,
            }}
          />
        </Source>
      )}
      {selected3dep && selectedNaip && datasetsIntersection && !result && (
        <Source
          id="bbox-intersection-source"
          type="geojson"
          data={datasetsIntersection}
        >
          <Layer
            id="bbox-intersection-layer"
            type="fill"
            paint={{ 'fill-color': '#a855f7', 'fill-opacity': 0.5 }}
          />
          <Layer
            id="bbox-intersection-border"
            type="line"
            paint={{
              'line-color': '#fde047',
              'line-width': 2,
              'line-dasharray': [4, 2],
            }}
          />
        </Source>
      )}
      {result && result?.[viewMode] && (
        <Source
          key={viewMode}
          id={`${viewMode}-source`}
          type="raster"
          tiles={[
            `/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@2x?url=${
              result[viewMode].href
            }&${result[viewMode].rescale}${
              viewMode !== 'naip' ? '&colormap_name=jet' : ''
            }`,
          ]}
          maxzoom={24}
          minzoom={0}
          tileSize={512}
        >
          <Layer
            id={`${viewMode}-layer`}
            type="raster"
            source={result.session_id}
          />
        </Source>
      )}
      <DrawToolbar
        aoi={aoi}
        result={result}
        setAoi={setAoi}
        setDatasets={setDatasets}
      />
    </Map>
  );
}
