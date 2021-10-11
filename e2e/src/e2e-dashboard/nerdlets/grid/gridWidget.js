/**
 * @description
 * @file
 * So far I've mostly used this as a tool to explore how exactly NR works with queries and
 * what's the shape of the data coming back from different queries.
 *
 * Execution plan for building out "Environment stability" dashboard:
 * 1. Get the list of all recent runs which ran against the 'main' branch of the repo.
 *    So far it just means getting the morning & deployment runs.
 * 2. Get a summary of pass rate per-file for each of those runs, kind of what we have right now.
 * 3. Display it in a grid view.
 * 4. Allow users to use PlatformState & queries to manipulate the results.
 *
 * Overall, we have all the freedom in the world to do whatever we want here,
 * but it's a bit disorienting. I.e. we could just pull raw events and do all of the data
 * manipulations on the client, it's potentially slow given enough data, but we rarely go
 * past a few thousand of reported events per day per environment. At the same time, we
 * could do multiple queries in a row to let NewRelic do the heavy-lifting on the data
 * manipulation side.
 */

import React from "react";
import { NrqlQuery, Spinner } from "nr1";
import { generateErrorsAndConfig, buildOrderedData } from "./utils";
import EmptyState from "./emptyState";
import ErrorState from "./errorState";
import ModalCharts from "./modalCharts";

// if the width is below this figure particular features will be disable
export const reducedFeatureWidth = 175;

export default class GridWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      modalOpen: false,
      initialized: false,
      timeRange: undefined,
      timeRangeResult: null,
    };
  }

  componentDidMount() {
    this.handleTime(this.props.timeRange);
  }

  componentDidUpdate() {
    this.handleTime(this.props.timeRange);
  }
  // This is supposed to handle changes of PlatformStateContext, like the default timeRange
  // it's currently not used in the main body of code.
  handleTime = async (incomingTimeRange) => {
    const currentTimeRange = this.state.timeRange;
    const currentTimeRangeStr = JSON.stringify(currentTimeRange);
    const incomingTimeRangeStr = JSON.stringify(incomingTimeRange);

    if (!incomingTimeRange && incomingTimeRangeStr !== currentTimeRangeStr) {
      this.setState({ timeRange: undefined, timeRangeResult: null });
    } else if (
      JSON.stringify(currentTimeRange) !== JSON.stringify(incomingTimeRange)
    ) {
      const stateUpdate = { timeRange: incomingTimeRange };
      const { query, accountId } = this.props;
      const nrqlResult = await NrqlQuery.query({
        query,
        accountId,
        timeRange: incomingTimeRange,
      });
      stateUpdate.timeRangeResult = nrqlResult?.data?.[0]?.data?.[0]?.y || null;
      this.setState(stateUpdate);
    }
  };

  modalClose = () => {
    this.setState({ modalOpen: false });
  };

  render() {
    const { modalOpen, initialized } = this.state;
    const {
      width,
      height,
      accountId,
      query,
      thresholds,
      onClickUrl,
      modalQueries,
      hideMetrics,
      decimalPlaces,
      hideKey,
    } = this.props;
    const validModalQueries = (modalQueries || []).filter(
      (q) => q.query && q.chartType && q.query.length > 5
    );

    const { errors, sortedThresholds } = generateErrorsAndConfig(
      thresholds,
      accountId,
      query,
      onClickUrl,
      validModalQueries
    );

    if (errors.length > 0) {
      return (
        <EmptyState
          errors={errors}
          reducedFeatureWidth={reducedFeatureWidth}
          isTimeline
        />
      );
    }

    // let finalQuery = `${query} ${timeseriesValue} `;
    let finalQuery = query;

    if (
      !query.toLowerCase().includes("since") &&
      !query.toLowerCase().includes("until")
    ) {
      // switched off for testing
      // finalQuery += ` ${sinceClause} ${untilValue}`;
      // We are using this instead of platform state time range.
      finalQuery += ` SINCE today`;
    }
    console.log(`Query: ${finalQuery}`);

    let chartOnClick;

    if (onClickUrl) {
      chartOnClick = () => window.open(onClickUrl, "_blank");
    }

    if (validModalQueries.length > 0) {
      const nerdlet = {
        id: "custom-modal",
        urlState: {
          accountId: parseInt(accountId),
          queries: validModalQueries,
          timeRange,
          height,
          width,
        },
      };

      chartOnClick = () => navigation.openStackedNerdlet(nerdlet);
    }

    return (
      <>
        <ModalCharts
          open={modalOpen}
          close={this.modalClose}
          queries={validModalQueries}
          accountId={accountId}
        />
        <NrqlQuery
          // Get latest test runs for a given env
          query={
            "SELECT uniques(runId) from CypressTestResult WHERE environment='test' SINCE today"
          }
          accountId={parseInt(accountId)}
          pollInterval={NrqlQuery.AUTO_POLL_INTERVAL}
        >
          {({ data, loading, error }) => {
            if (loading) return <Spinner />;
            if (error)
              return (
                <ErrorState
                  error={error.message || ""}
                  query={
                    "SELECT uniques(runId) from CypressTestResult WHERE environment='test' SINCE 1 day ago"
                  }
                  reducedFeatureWidth={reducedFeatureWidth}
                />
              );
            console.log(data[0]?.data);
            return <pre>{JSON.stringify(data, null, 2)}</pre>;
          }}
        </NrqlQuery>
        <NrqlQuery
          query={finalQuery}
          accountId={parseInt(accountId)}
          pollInterval={NrqlQuery.AUTO_POLL_INTERVAL}
        >
          {({ data, loading, error }) => {
            if (loading) {
              return <Spinner />;
            }

            if (error && initialized === false) {
              return (
                <ErrorState
                  error={error.message || ""}
                  query={finalQuery}
                  reducedFeatureWidth={reducedFeatureWidth}
                />
              );
            }

            if (initialized === false) {
              this.setState({ initialized: true });
            }

            const { orderedData, xLabels } = buildOrderedData(
              data,
              query,
              sortedThresholds
            );

            return (
              <div
                style={{
                  width,
                  height,
                  maxWidth: width,
                  maxHeight: height,
                }}
              >
                <pre>{JSON.stringify(orderedData, null, 2)}</pre>
                <table
                  style={{
                    width: "100%",
                    bottom: hideKey ? undefined : "30px",
                  }}
                >
                  {Object.keys(orderedData).map((key) => {
                    const data = orderedData[key];
                    return (
                      <tr key={key}>
                        <td>{key === "undefined" ? "Other" : key}</td>
                        {Object.keys(data).map((key2) => {
                          const { bgColor, fontColor } = data[key2];
                          let value = data[key2].value;
                          if (
                            decimalPlaces !== null &&
                            decimalPlaces !== undefined
                          ) {
                            value = value.toFixed(parseInt(decimalPlaces));
                          }

                          return (
                            <td
                              key={key2}
                              style={{
                                backgroundColor: bgColor,
                                color: fontColor,
                              }}
                            >
                              {!hideMetrics && value}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                  <tr>
                    <td
                      style={{
                        position: "sticky",
                        bottom: hideKey ? "0px" : "30px",
                      }}
                    />
                    {xLabels.map((label) => {
                      return (
                        <td
                          key={label}
                          style={{
                            position: "sticky",
                            bottom: hideKey ? "0px" : "30px",
                          }}
                        >
                          {label}
                        </td>
                      );
                    })}
                  </tr>
                </table>

                {!hideKey && (
                  <div
                    style={{
                      position: "sticky",
                      bottom: "0px",
                      textAlign: "center",
                      padding: "10px",
                      backgroundColor: "white",
                    }}
                  >
                    {thresholds.map((t) => {
                      const value = {};
                      const { bgColor, fontColor } = t;

                      if (bgColor === "healthy" || bgColor === "green") {
                        value.bgColor = "#01b076";
                        value.fontColor = "white";
                      }

                      if (fontColor === "healthy" || fontColor === "green") {
                        value.fontColor = "#01b076";
                      }

                      if (bgColor === "critical" || bgColor === "red") {
                        value.bgColor = "#f5554b";
                        value.fontColor = "white";
                      }

                      if (fontColor === "critical" || fontColor === "red") {
                        value.fontColor = "#f5554b";
                      }

                      if (bgColor === "warning" || bgColor === "orange") {
                        value.bgColor = "#f0b400";
                        value.fontColor = "white";
                      }

                      if (fontColor === "warning" || fontColor === "orange") {
                        value.fontColor = "#f0b400";
                      }

                      if (bgColor === "unknown" || bgColor === "grey") {
                        value.bgColor = "#9fa5a5";
                      }

                      if (fontColor === "unknown" || fontColor === "grey") {
                        value.fontColor = "#9fa5a5";
                      }

                      return (
                        <>
                          <div style={{ display: "inline" }}>
                            <span style={{ color: value.bgColor }}>
                              &#9632;
                            </span>
                            &nbsp;
                            {t.name}
                          </div>
                          &nbsp;&nbsp;&nbsp;
                        </>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          }}
        </NrqlQuery>
      </>
    );
  }
}
