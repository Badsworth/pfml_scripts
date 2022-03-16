import React from "react";
import { setDefault } from "../common";
import RichErroMessage from "../common/components/RichErroMessage";
import { TestGridHeader } from "./TestGrid";

export class GridRow extends React.Component {
  state = {
    open: false,
  };

  constructor(props) {
    super(props);
    this.spec = props.spec;
    this.file = props.file;
    this.runs = props.runs;

    this.runs.map(({ runId }) => {
      this.calculateFileStatus(runId);
    });
  }

  progressStyle = (runOverview) => {
    let width;
    if (runOverview.percent === null || runOverview.status === "skip") {
      width = 100;
    } else {
      width = runOverview.percent;
    }

    return { width: `${width}%` };
  };

  progressDisplay(runOverview) {
    if (runOverview.percent === null) {
      return "N/A";
    } else if (runOverview.status === "skip") {
      return "SKIP";
    } else if (runOverview.percent === 100) {
      return "PASS";
    } else {
      return `${runOverview.percent}%`;
    }
  }

  progressClass(runOverview) {
    if (runOverview.status === null) {
      return "na";
    } else if (runOverview.status === "pass") {
      if (runOverview.totalTries > runOverview.totalBlocks) {
        return "flake";
      }
      if (runOverview.skip) {
        return "skip";
      }
    }

    return runOverview.status;
  }

  getOverallStatus = (runOverview) => {
    if (runOverview === "unknown" || runOverview?.totalBlocks === 0) {
      return `N/A`;
    }

    if (runOverview.totalBlocks === runOverview.pass) {
      return "PASS";
    } else {
      return `${Math.round(
        (runOverview.pass / runOverview.totalBlocks) * 100
      )}%`;
    }
  };

  /**
   * Calculate the overall status of the run for this file.
   * We needed to do this after all data was populated.
   *
   * @param runId
   * @returns {string}
   */
  calculateFileStatus(runId) {
    let _rOverview = this.spec.overview[runId];

    _rOverview.percent = null;
    if (_rOverview?.totalBlocks !== 0) {
      _rOverview.percent = Math.round(
        (_rOverview.pass / _rOverview.totalBlocks) * 100
      );
    }

    // Iterate through all blocks in the run, and determine the overall status
    _rOverview.status = Object.keys(this.spec.blocks).reduce((s, block) => {
      const runStatus = this.spec.blocks[block].runs[runId].status;
      //First Iteration
      if (s === null) {
        return runStatus;
      }
      //Fail always wins status
      if (runStatus === "fail") {
        return runStatus;
      }
      if (s === "skip" && runStatus === "pass") {
        return runStatus;
      }
      return s;
    }, null);
  }

  toggleShow(id) {
    if (id == null) {
      this.setState((state) => {
        return (state.open = !state.open);
      });
    } else {
      this.setState((state) => {
        if (!state[id]) {
          state[id] = { open: false };
        }
        return (state[id].open = !state[id].open);
      });
    }
  }

  render() {
    if (!this.spec) {
      return <span></span>;
    }
    return [
      <tr className="highlight">
        <td
          className={`filename ${this.progressClass(
            this.spec.overview[this.runs[0].runId]
          )}`}
          onClick={() => {
            this.toggleShow(null);
          }}
        >
          {this.file}
        </td>
        {this.runs.map(({ runId }) => {
          const runOverview = this.spec.overview[runId];
          return [
            <td />,
            <td>
              <div
                className={`runProgress clickable ${this.progressClass(
                  runOverview
                )}`}
              >
                <div
                  className={`progress ${this.progressClass(runOverview)}`}
                  style={this.progressStyle(runOverview)}
                >
                  {this.progressDisplay(runOverview)}
                </div>
              </div>
            </td>,
          ];
        })}
      </tr>,
      <tr className={this.state.open ? "open" : "closed"}>
        <td className="subTable" colSpan={this.runs.length * 2 + 2}>
          <table className={"runDetails"}>
            {this.runs.length > 1 && (
              <thead>
                <tr>
                  {this.runs.map((run, i) => [
                    <th
                      className={this.progressClass(
                        this.spec.overview[run.runId]
                      )}
                    >
                      <TestGridHeader run={run} index={i} date={false} />
                    </th>,
                  ])}
                </tr>
              </thead>
            )}
            <tbody>
              {Object.keys(this.spec.blocks)
                .sort(
                  (a, b) =>
                    this.spec.blocks[a].order - this.spec.blocks[b].order
                )
                .map((key) => {
                  let status = null;
                  const block = this.spec.blocks[key];
                  if (this.runs.length === 1) {
                    status =
                      block.runs[this.runs[0].runId].status.toUpperCase();
                  }
                  return [
                    <tr>
                      <td colSpan={this.runs.length} className="blockTitle">
                        {this.runs.length === 1 && (
                          <span className={`pill ${status}`}>{status}</span>
                        )}
                        {key}
                      </td>
                    </tr>,
                    <tr>
                      {this.runs.map(({ runId }) => {
                        const run = block.runs[runId];
                        return (
                          <GridRowDetails
                            run={run}
                            singleRun={status !== null}
                          />
                        );
                      })}
                    </tr>,
                  ];
                })}
            </tbody>
          </table>
        </td>
      </tr>,
    ];
  }
}

function GridRowDetails({ run, singleRun }) {
  const status = run.status ? run.status.toUpperCase() : "N/A";
  singleRun = setDefault(singleRun, false);
  return (
    <td className="TestGridRowDetails">
      <table className="TestGridRowDetails">
        {(run.messages.length > 0 && !singleRun) ||
          (!singleRun && (
            <tr>
              <td colSpan="2">
                <span className={`pill ${status}`}>{status}</span>
                {`${run.category ?? ""}`}
              </td>
            </tr>
          ))}
        <GridRowMessages run={run} singleRun={singleRun} />
      </table>
    </td>
  );
}

function GridRowMessages({ run, singleRun }) {
  if (!run.messages.length) {
    return <></>;
  }
  return run.messages.map(({ tryNumber, message }, i) => {
    if (message) {
      return (
        <tr className={`try ${run.status} try_${tryNumber}`}>
          {!singleRun && i === 0 && (
            <td
              className={`status ${run.status}`}
              rowSpan={run.messages.length}
            >
              <span>{run.status}</span>
            </td>
          )}
          <td className="tryNumber">{tryNumber}</td>
          <td className={run.status ?? "closed"}>
            <code className={"display-linebreak"}>
              <RichErroMessage>{message}</RichErroMessage>
            </code>
          </td>
        </tr>
      );
    }
  });
}
