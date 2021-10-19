import config from "./config";

export type Layout = {
  column?: number;
  row?: number;
  height?: number;
  width?: number;
};

const accountId = parseInt(config("NEWRELIC_ACCOUNTID"));

/**
 * Make a New Relic visualization object for a table.
 *
 * @param title
 * @param query
 * @param layout
 */
export function makeTableViz(
  title: string,
  query: string,
  layout?: Layout
): Record<string, unknown> {
  return {
    visualization: {
      id: "viz.table",
    },
    layout,
    title,
    rawConfiguration: {
      dataFormatters: [],
      facet: {
        showOtherSeries: false,
      },
      nrqlQueries: [
        {
          accountId,
          query,
        },
      ],
    },
    linkedEntityGuids: null,
  };
}

/**
 * Make billboard visualization object.
 * Make warning threshold bigger than critical threshold if you want the billboard to highlight once it's below a certain value.
 * @param title
 * @param query
 * @param warningThreshold viz will highlight yellow once past this threshold
 * @param criticalThreshold viz will highlight red once past this threshold
 * @param layout
 * @returns
 */
export function makeBillboardViz(
  title: string,
  query: string,
  warningThreshold: number,
  criticalThreshold: number,
  layout?: Layout
): Record<string, unknown> {
  return {
    visualization: {
      id: "viz.billboard",
    },
    layout,
    title,
    rawConfiguration: {
      dataFormatters: [],
      nrqlQueries: [
        {
          accountId,
          query,
        },
      ],
      thresholds: [
        {
          alertSeverity: "CRITICAL",
          value: criticalThreshold,
        },
        {
          alertSeverity: "WARNING",
          value: warningThreshold,
        },
      ],
    },
    linkedEntityGuids: null,
  };
}

export type Threshold = {
  bgColor: string;
  fontColor: string | null;
  name: string;
  priority: number | null;
  valueAbove: number | null;
  valueBelow: number | null;
  valueEqual: number | null;
};

/**
 * Make status timeline visualization object.
 * @param title
 * @param query
 * @param decimalPlaces
 * @param hideKey
 * @param hideMetrics
 * @param thresholds
 * @param layout
 * @returns
 */
export function makeStatusTimelineViz(
  title: string,
  query: string,
  decimalPlaces: number,
  hideKey: boolean,
  hideMetrics: boolean,
  thresholds?: Threshold[],
  layout?: Layout
): Record<string, unknown> {
  return {
    visualization: {
      id: "d997a1e4-423d-4d01-b450-da8a4465f60e.status-timeline-widget",
    },
    layout,
    title,
    rawConfiguration: {
      accountId: 2837112,
      decimalPlaces,
      hideKey,
      hideMetrics,
      query,
      thresholds,
    },
    linkedEntityGuids: null,
  };
}
