import React from "react";
import { ENVS, setDefault } from "../index";
import { E2EQuery } from "./E2EQuery";
import { DAO } from "../DAO";

export class MorningReport extends React.Component {
  state = {
    envs: ENVS,
    since: "",
    where: "",
    simpleView: true,
  };

  static getDerivedStateFromProps(props) {
    return {
      envs: setDefault(props.envs, ENVS),
      since: setDefault(props.since, "1 month ago UNTIL NOW"),
      where: setDefault(props.where, ""),
      simpleView: setDefault(props.simpleView, true),
    };
  }

  constructor(props) {
    super(props);
    this.accountId = props.accountId;
  }

  getIds(runs) {
    return Object.keys(runs).reduce((arr, key) => {
      const value = runs[key];
      arr.push(value);
      if (value?.includes("-failed-specs")) {
        arr.push(value.replace("-failed-specs", ""));
      }
      return arr;
    }, []);
  }

  render() {
    if (this.state.envs.length === 0) {
      return <span>Select Filter</span>;
    }

    return [
      <E2EQuery
        DAO={DAO.LastRunIdPerEnv()
          .envs(this.state.envs)
          .where(this.state.where)
          .since(this.state.since)}
      >
        {({ data: { 0: runs } }) => {
          const runIds = this.getIds(runs);
          return (
            <span>
              <E2EQuery
                DAO={DAO.MorningRun().runIds(runIds).since(this.state.since)}
              >
                {({ data: morning }) => {
                  return (
                    <div className="MorningReport">
                      <h1>Morning Report</h1>
                      <br />
                      <br />
                      <b>Environment check (cypress) :memo:</b>
                      <br />
                      <b>Clean runs w/o errors (from auto Morning Runs)</b> ✅✅
                      <br />
                      <ul>
                        {morning.stable.clean.map((value) => (
                          <li>
                            <code>{value}</code>
                          </li>
                        ))}
                      </ul>
                      <b>Clean runs w/retry:</b>
                      <br />
                      <ul>
                        {morning.stable.cleanRerun.map((value) => (
                          <li>
                            <code>{value}</code>
                          </li>
                        ))}
                      </ul>
                      <b>Envs w/expected failures (No set date):</b> ❌❌
                      <br />
                      <ul>
                        <li></li>
                      </ul>
                      <b>Important Tickets and/or EDMs created:</b>{" "}
                      :information_source:
                      <br />
                      <ul>
                        {morning.stable.failed.map((value) => [
                          <li>EDM</li>,
                          <li>
                            <ul>
                              <li>
                                <code>{value}</code>
                              </li>
                            </ul>
                          </li>,
                        ])}
                      </ul>
                      <span>
                        ***************************************************************************************
                        <br />
                      </span>
                      <b>Environment check (Integration) :memo:</b>
                      <br />
                      <b>Clean runs w/o errors </b> ✅✅{" "}
                      <i>(All lower envs :raised_hands:)</i>
                      <br />
                      <ul>
                        {morning.integration.clean.map((value) => (
                          <li>
                            <code>{value}</code>
                          </li>
                        ))}
                      </ul>
                      <b>Clean runs w/retry:</b>
                      <br />
                      <ul>
                        {morning.integration.cleanRerun.map((value) => (
                          <li>
                            <code>{value}</code>
                          </li>
                        ))}
                      </ul>
                      <b>Envs w/expected failures (No set date):</b> ❌❌
                      <br />
                      <ul>
                        <li></li>
                      </ul>
                      <b>Important Tickets and/or EDMs created:</b>{" "}
                      :information_source:
                      <br />
                      <ul>
                        {morning.integration.failed.map((value) => [
                          <li>EDM</li>,
                          <li>
                            <ul>
                              <li>
                                <code>{value}</code>
                              </li>
                            </ul>
                          </li>,
                        ])}
                      </ul>
                      <span>
                        ***************************************************************************************
                        <br />
                      </span>
                      <b>Environment check (Morning) :memo:</b>
                      <br />
                      <b>Clean runs w/o errors </b> ✅✅{" "}
                      <i>(All lower envs :raised_hands:)</i>
                      <br />
                      <ul>
                        {morning.morning.clean.map((value) => (
                          <li>
                            <code>{value}</code>
                          </li>
                        ))}
                      </ul>
                      {morning.morning.failed.length && (
                        <span>
                          <b>Important Tickets and/or EDMs created:</b>{" "}
                          :information_source:
                          <br />
                          <ul>
                            {morning.morning.failed.map((value) => [
                              <li>EDM</li>,
                              <li>
                                <ul>
                                  <li>
                                    <code>{value}</code>
                                  </li>
                                </ul>
                              </li>,
                            ])}
                          </ul>
                        </span>
                      )}
                    </div>
                  );
                }}
              </E2EQuery>
            </span>
          );
        }}
      </E2EQuery>,
    ];
  }
}
