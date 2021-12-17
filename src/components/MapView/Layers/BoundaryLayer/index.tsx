import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { get } from 'lodash';
import { GeoJSONLayer } from 'react-mapbox-gl';
import * as MapboxGL from 'mapbox-gl';
import { showPopup } from '../../../../context/tooltipStateSlice';
import { BoundaryLayerProps } from '../../../../config/types';
import { LayerData } from '../../../../context/layers/layer-data';
import {
  loadDataset,
  DatasetParams,
} from '../../../../context/layers/boundary';
import { layerDataSelector } from '../../../../context/mapStateSlice/selectors';

function onToggleHover(cursor: string, targetMap: MapboxGL.Map) {
  // eslint-disable-next-line no-param-reassign, fp/no-mutation
  targetMap.getCanvas().style.cursor = cursor;
}

function BoundaryLayer({ layer }: { layer: BoundaryLayerProps }) {
  const dispatch = useDispatch();
  const boundaryLayer = useSelector(layerDataSelector(layer.id)) as
    | LayerData<BoundaryLayerProps>
    | undefined;
  const { data } = boundaryLayer || {};

  if (!data) {
    return null; // boundary layer hasn't loaded yet. We load it on init inside MapView. We can't load it here since its a dependency of other layers.
  }

  const onClickFunc = (evt: any) => {
    const coordinates = evt.lngLat;

    const { properties } = evt.features[0];

    const locationName = layer.adminLevelNames
      .map(level => get(properties, level, '') as string)
      .join(', ');
    dispatch(showPopup({ coordinates, locationName }));

    const datasetParams: DatasetParams = {
      id: properties[layer.adminCode],
      filepath: 'data/mozambique/tables/moz-r1h-adm2-transposed.csv',
    };

    dispatch(loadDataset(datasetParams));
  };

  return (
    <GeoJSONLayer
      id={layer.id === 'admin_boundaries' ? 'boundaries' : layer.id}
      data={data}
      fillPaint={layer.styles.fill}
      linePaint={layer.styles.line}
      fillOnMouseEnter={(evt: any) => onToggleHover('pointer', evt.target)}
      fillOnMouseLeave={(evt: any) => onToggleHover('', evt.target)}
      fillOnClick={layer.id === 'admin_boundaries' ? onClickFunc : undefined}
    />
  );
}

export default BoundaryLayer;
