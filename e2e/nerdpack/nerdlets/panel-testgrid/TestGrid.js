import { Tooltip } from "nr1";
import React from "react";
import { labelEnv } from "../common";
import { E2EQuery } from "../common/components/E2EQuery";
import { DAO, DAORunDetails } from "../common/DAO";
import { Tags } from "../common/components/Tags";
import { format } from "date-fns";

class GridRow extends React.Component {
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
    } else if (runOverview.percent === "pass") {
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

  render() {
    if (!this.spec) {
      return <span></span>;
    }
    return [
      <tr>
        <td>
          <span
            className={`indicator ${this.progressClass(
              this.spec.overview[this.runs[0].runId]
            )}`}
          />
        </td>
        <td className="filename">{this.file}</td>
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
    ];
  }
}

export default class TestGrid extends React.Component {
  constructor(props) {
    super(props);
    this.runIds = props.runIds;
  }

  msToTime(duration) {
    var milliseconds = Math.floor((duration % 1000) / 100),
      seconds = Math.floor((duration / 1000) % 60),
      minutes = Math.floor((duration / (1000 * 60)) % 60),
      hours = Math.floor((duration / (1000 * 60 * 60)) % 24);

    hours = hours < 10 ? "0" + hours : hours;
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;

    return hours + ":" + minutes + ":" + seconds + "." + milliseconds;
  }

  /**
   * Get a list of envs that are being compared (will usually just be 1)
   * @param overview
   * @returns {string}
   */
  displayEnvs(overview) {
    return [
      ...overview.reduce(
        (arr, run) => arr.add(labelEnv(run.environment)),
        new Set()
      ),
    ].join(", ");
  }
  render() {
    const stableDAO = DAO.RunDetails().setTestGridWhere(
      this.runIds,
      Object.values(DAORunDetails.GROUP_TYPE)
    );

    if (this.runIds) {
      return (
        <table className={"testGridTable"}>
          <E2EQuery DAO={stableDAO}>
            {({ data: stable }) => {
              const { overview, groups } = this.processData(stable);
              return Object.keys(groups)
                .sort()
                .map((groupName) => {
                  const files = groups[groupName].files;
                  return [
                    <thead>
                      <tr>
                        <th colSpan="30">
                          <h2>
                            {groupName} - {this.displayEnvs(overview)}
                          </h2>
                        </th>
                      </tr>
                      <tr>
                        <th />
                        <th>File</th>
                        {overview.map((run, i) => [
                          <th />,
                          <th width="150px" className="colProgress">
                            <Tooltip
                              placementType={Tooltip.PLACEMENT_TYPE.BOTTOM}
                              text={`${format(run.startTime, "PPp")} - ${format(
                                run.endTime,
                                "PPp"
                              )}\n
                              Run ID: ${run.runId}
                              Environment: ${labelEnv(run.environment)}
                              Compute Time: ${this.msToTime(run.computeTimeMs)}
                              `}
                              additionalInfoLink={{
                                to: run.cypressUrl,
                                label: "View in Cypress",
                              }}
                            >
                              <span>
                                {i + 1}
                                <Tags tags={run.tags} />
                                <span className="date">
                                  {format(run.startTime, "PPp")}
                                </span>
                              </span>
                            </Tooltip>
                          </th>,
                        ])}
                      </tr>
                    </thead>,
                    <tbody>
                      {Object.keys(files)
                        .sort()
                        .map((file) => (
                          <GridRow
                            spec={files[file]}
                            file={file}
                            runs={overview}
                          />
                        ))}
                    </tbody>,
                  ];
                });
            }}
          </E2EQuery>
        </table>
      );
    }
    return <span>NO Data</span>;
  }

  //TODO: Move data manipulation to model|service files
  newOverview(runId) {
    return {
      runId: runId,
      cypressUrl: null,
      githubActionUrl: null,
      environment: null,
      tags: [],
      branch: "",
      startTime: null,
      endTime: null,
      computeTimeMs: 0,
    };
  }

  newFile(runOverview) {
    return {
      overview: runOverview.reduce((obj, run) => {
        obj[run.runId] = {
          totalBlocks: 0,
          totalTries: 0,
          pass: 0,
          skip: 0,
          fail: 0,
          category: "",
          status: null,
        };
        return obj;
      }, {}),
      blocks: {},
    };
  }

  newBlock(runOverview, order) {
    return {
      order: order,
      runs: runOverview.reduce((obj, run) => {
        obj[run.runId] = {
          status: null,
          category: null,
          tryNumber: 0,
          messages: [],
          check: [],
        };
        return obj;
      }, {}),
    };
  }

  statusFromObj(obj) {
    if (obj.pass) {
      return "pass";
    }
    if (obj.fail) {
      return "fail";
    }
    if (obj.skip) {
      return "skip";
    }
  }

  /**
   *
   * @param data
   * @return
   * {
   *   overview:[
   *     {
   *       runId: "",
   *       cypressUrl: null,
   *       githubActionUrl: null,
   *       environment: null,
   *       tags: [],
   *       branch:"",
   *       startTime:"",
   *       endTime:"",
   *       computeTimeMs: 0,
   *     };
   *   ]
   *   group:{
   *     "<GROUP>": {
   *       files:{
   *         "<FILENAME>": {
   *           overview: {
   *             "<runid>": {
   *               totalBlocks: 0,
   *               totalTries: 0,
   *               pass: 0,
   *               skip: 0,
   *               fail: 0,
   *               category: "",
   *               status: "",
   *             },
   *           },
   *           blocks: {
   *             "<name>": {
   *               order: 0,
   *               runs:{
   *                 "<runid>": {
   *                   status: "pass/fail/skip",
   *                   category: "",
   *                   messages: [
   *                     {
   *                       message: "",
   *                       try: "",
   *                     },
   *                   ],
   *                 },
   *               },
   *             },
   *           },
   *         },
   *       },
   *     },
   *   }
   * }
   */
  processData(data) {
    let runOverview = this.runIds.map((id) => {
      return this.newOverview(id);
    });
    let ret = {};

    /**
     * Sample Record:
     * -------------------
     * anonymizedMessage: "`cy.task('submitClaimToAPI')` failed with the following error:\n\n"
     * blockTitle: "Given a fully approved claim"
     * branch: "main"
     * duration: 36343
     * environment: "breakfix"
     * fail: true
     * file: "cypress/specs/stable/feature/api_caring_continuous_approval_extensionNotification+O_RButtons.ts"
     * group: "Commit Stable"
     * pass: false
     * runId: "EOLWD/pfml-1898273937-1"
     * runUrl: "https://dashboard.cypress.io/projects/wjoxhr/runs/10752"
     * schemaVersion: 0.2
     * skip: false
     * status: "failed"
     * tag: "Morning Run,Env-breakfix"
     * timestamp: 1645787200206
     * tryNumber: 2
     */

    data.forEach((datum) => {
      const file = datum.file.replace("cypress/specs/", "");
      const group = DAORunDetails.groupTypeLookup(datum.group, file);

      // Setup Group
      if (!ret[group]) {
        ret[group] = {
          files: {},
        };
      }
      let _group = ret[group].files;

      // Setup File
      if (!_group[file]) {
        _group[file] = this.newFile(runOverview);
      }
      let _overview = _group[file].overview[datum.runId];

      // Setup Block
      if (!_group[file].blocks[datum.blockTitle]) {
        _group[file].blocks[datum.blockTitle] = this.newBlock(
          runOverview,
          Object.keys(_group[file].blocks).length
        );
      }

      /**
       * Update Run Overview
       */
      let _rOverview = runOverview.find((v) => v.runId === datum.runId);
      _rOverview.cypressUrl = datum.runUrl;
      _rOverview.environment = datum.environment;

      if (datum.tag) {
        _rOverview.tags = datum.tag
          .split(",")
          .filter((tag) => !tag.includes("Env-"));
      }
      _rOverview.branch = datum.branch;
      _rOverview.computeTimeMs += datum.duration;

      const time = new Date(datum.timestamp);
      if (_rOverview.startTime === null || _rOverview.startTime > time) {
        _rOverview.startTime = time;
      }

      if (_rOverview.endTime === null || _rOverview.endTime < time) {
        _rOverview.endTime = time;
      }

      /**
       * Update File Overview Counts
       */
      _overview.totalTries++;
      if (datum.pass) {
        _overview.pass++;
      }
      if (datum.skip) {
        _overview.skip++;
      }
      if (datum.fail) {
        _overview.fail++;
      }

      /**
       * Update ItBlock Information
       */
      let _runBlock = _group[file].blocks[datum.blockTitle].runs[datum.runId];
      if (_runBlock.tryNumber < datum.tryNumber) {
        _runBlock.tryNumber = datum.tryNumber;
        _runBlock.status = this.statusFromObj(datum);
      }

      // Dont count a block for a run if it already has a message in it.
      if (!_runBlock.messages.length) {
        _overview.totalBlocks++;
      }

      _runBlock.messages.push({
        message: datum.anonymizedMessage,
        tryNumber: datum.tryNumber,
      });
    });

    return { overview: runOverview, groups: ret };
  }
}
