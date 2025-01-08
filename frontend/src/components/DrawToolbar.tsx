import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';
import { Feature, Geometry, GeoJsonProperties } from 'geojson';
import { useEffect } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import MapboxDraw, { DrawCreateEvent } from '@mapbox/mapbox-gl-draw';
import { IControl } from 'maplibre-gl';

import { drawStyles } from './drawStyles';

import { Datasets } from './MyMap';

type DrawToolbarProps = {
  setAoi: React.Dispatch<
    React.SetStateAction<Feature<Geometry, GeoJsonProperties> | null>
  >;
  setDatasets: React.Dispatch<React.SetStateAction<Datasets | null>>;
};

export default function DrawToolbar({ setAoi, setDatasets }: DrawToolbarProps) {
  const { current: map } = useMap();

  useEffect(() => {
    if (!map) return;

    // Solution to address missing mapbox classes
    // https://github.com/maplibre/maplibre-gl-js/issues/2601#issuecomment-1564747778
    map.getCanvas().className = 'mapboxgl-canvas maplibregl-canvas';
    map.getContainer().classList.add('mapboxgl-map');
    const canvasContainer = map.getCanvasContainer();
    canvasContainer.classList.add('mapboxgl-canvas-container');
    if (canvasContainer.classList.contains('maplibregl-interactive')) {
      canvasContainer.classList.add('mapboxgl-interactive');
    }

    const drawControl: MapboxDraw = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        polygon: true,
        trash: true,
      },
      defaultMode: 'draw_polygon',
      styles: drawStyles,
    });

    // Solution to address missing mapbox classes
    // https://github.com/maplibre/maplibre-gl-js/issues/2601#issuecomment-1564747778
    const originalOnAdd = drawControl.onAdd.bind(drawControl);
    drawControl.onAdd = (map) => {
      const controlContainer = originalOnAdd(map);
      controlContainer.classList.add('maplibregl-ctrl', 'maplibregl-ctrl-group');
      return controlContainer;
    };

    // drawControl is type MapboxDraw which has the required attributes
    // but `addControl` expects an IControl
    map.addControl(drawControl as unknown as IControl, 'top-left');

    map.on('draw.create', (e: DrawCreateEvent) => {
      async function sendAOI(feature: Feature) {
        try {
          const response = await fetch('/api/datasets', {
            method: 'post',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feature),
          });
          const result = await response.json();
          setDatasets(result);
          setAoi(feature);
        } catch (err) {
          console.error('Error:', err);
        }
      }
      sendAOI(e.features[0]);
    });

    return () => {
      // Remove mapbox draw control on dismount
      map.removeControl(drawControl as unknown as IControl);
    };
  }, [map]);

  return null;
}
