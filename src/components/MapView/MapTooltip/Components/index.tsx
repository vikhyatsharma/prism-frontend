import React from 'react';
import { PopupComponentSpec } from '../../../../context/tooltipStateSlice';
import Chartjs from './Chartjs';
import Fsva from './Fsva';
import RawHtml from './RawHtml';

const components = {
  Chartjs,
  Fsva,
  RawHtml,
} as {
  [key: string]: (props: PopupComponentSpec) => JSX.Element;
};

export default (props: PopupComponentSpec) => {
  const { type } = props;
  const Component = components[type];
  return <Component {...props} />;
};