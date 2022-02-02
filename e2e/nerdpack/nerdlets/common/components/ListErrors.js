import React from "react";
import { format } from "date-fns";
import { labelEnv, setDefault } from "../index";
import {
  Icon,
  Link,
  navigation,
  NrqlQuery,
  SectionMessage,
  Spinner,
  BillboardChart,
  Grid,
  GridItem,
  StackedBarChart,
} from "nr1";
import DOMPurify from "dompurify";

export class ListErrorsRow extends React.Component {
  state = {
    open: false,
    internal: false,
  };

  static getDerivedStateFromProps(props, current_state) {
    if (current_state && current_state.internal) {
      if (current_state.open != props.open) {
        return {
          open: current_state.open,
          internal: false,
        };
      }
    }
    return {
      open: props.open,
    };
  }

  constructor(props) {
    super(props);
    if (props.open) {
      this.state.open = props.open;
    }
    this.item = props.item;
  }

  toggleShow = () => {
    this.setState((state) => ({ open: !state.open, internal: true }));
  };

  render() {
    const item = this.item;
    return (
      <div className={"list-row row"}>
        <div className={"col"}>
          <div onClick={this.toggleShow} className={"row"}>
            <div className={"time"}>{format(item.timestamp, "PPPp")}</div>
            <div className={"environment"}>
              {labelEnv(item.environment)}
              {item.environment}
            </div>
            <div className={"tags"}>
              {item?.tag
                .split(",")
                .filter((tag) => !tag.includes("Env-") && tag != "Deploy")
                .map((tag) => (
                  <span
                    className={`${tag
                      .split("-")
                      .join(" ")
                      .toLowerCase()} label`}
                  >
                    {tag}
                  </span>
                ))}
            </div>
            <div className={"category"}>
              {item?.category} {item?.subCategory}
            </div>

            <Icon
              className={"right"}
              style={{ display: `${this.state.open ? "none" : "block"}` }}
              type={Icon.TYPE.INTERFACE__CHEVRON__CHEVRON_TOP__V_ALTERNATE}
            ></Icon>
            <Icon
              className={"right"}
              style={{ display: `${this.state.open ? "block" : "none"}` }}
              type={Icon.TYPE.INTERFACE__CHEVRON__CHEVRON_BOTTOM__V_ALTERNATE}
            ></Icon>
          </div>
          <div className={"row"}>
            <div className={"runlink"}>
              <Link
                to={navigation.getOpenStackedNerdletLocation({
                  id: "e2e-tests",
                  urlState: { runIds: [item.runId] },
                })}
              >
                Open Run Dashboard
              </Link>
            </div>
            <div className={"runlink"}>
              <Link to={item.runUrl}>View in Cypress</Link>
            </div>
            <div className={"file right"}>
              {item.file.replace("cypress/specs/", "")}
            </div>
          </div>
          <div
            className={`errorMessage ${this.state.open ? "open" : "closed"}`}
          >
            <span className={"suite"}>
              <strong>SUITE:</strong>
              {item.suite}
            </span>
            <br />
            <span className={"test"}>
              <strong>TEST: </strong>
              {item.test}
            </span>
            <br />
            <br />
            <span className={"fileError"}>
              {item.errorClass} In file {item.errorRelativeFile} @ line{" "}
              {item.errorLine}
            </span>
            <br />
            <br />
            <span
              dangerouslySetInnerHTML={{
                __html: DOMPurify.sanitize(
                  item.errorMessage?.replace(/[\r\n]+/g, "<br>"),
                  {
                    ALLOWED_TAGS: ["br"],
                  }
                ),
              }}
            />
          </div>
        </div>
      </div>
    );
  }
}

export class ListErrors extends React.Component {
  state = {
    query: "",
    open: false,
  };

  static getDerivedStateFromProps(props) {
    return {
      query: props.query,
      open: props.open,
    };
  }

  constructor(props) {
    super(props);
    this.accountId = props.accountId;
    this.scrollable = setDefault(props.scrollable, true);
  }

  render() {
    return (
      <NrqlQuery accountId={this.accountId} query={this.state.query}>
        {({ data: listData, loading, error }) => {
          if (loading) {
            return <Spinner />;
          }
          if (error) {
            return (
              <SectionMessage
                title={"There was an error executing the query"}
                description={error.message}
                type={SectionMessage.TYPE.CRITICAL}
              />
            );
          }

          if (!listData.length) {
            return <div>No Data</div>;
          }

          return (
            <div
              className={`ListErrors ${this.scrollable ? "scrollable" : ""}`}
            >
              {listData[0].data.map((item) => {
                return (
                  <ListErrorsRow
                    item={item}
                    open={this.state.open}
                  ></ListErrorsRow>
                );
              })}
            </div>
          );
        }}
      </NrqlQuery>
    );
  }
}

export class ErrorsListWithOverview extends React.Component {
  state = {
    since: "",
    where: "",
    open: true,
  };

  static getDerivedStateFromProps(props, current_state) {
    if (current_state) {
      if (current_state.open != props.open) {
        return {
          open: current_state.open,
          since: props.since,
          where: props.where,
        };
      }
    }
    return {
      since: props.since,
      where: props.where,
    };
  }

  constructor(props) {
    super(props);
    this.accountId = props.accountId;
    this.scrollable = setDefault(props.scrollable, true);
    this.overview = setDefault(props.overview, true);
    this.children = props.children;
  }

  toggleShow = () => {
    this.setState((state) => ({ open: !state.open }));
  };

  render() {
    const query = `FROM CypressTestResult
                   WHERE pass is false
                      ${this.state.where ? "AND" : ""} ${this.state.where}
                   ${this.state.since ? "SINCE" : ""} ${this.state.since}
                   LIMIT MAX`;
    const querySelect = `SELECT * ${query}`;
    const queryCount = `SELECT count(*) as Total ${query}`;
    const queryBarClass = `SELECT count(*) as Total ${query} FACET category, subCategory`;
    return (
      <Grid className={"E2E-error-list"}>
        <GridItem className={"ListHeader"} columnSpan={12}>
          {this.children ? this.children : <h1>All Errors</h1>}
          <button onClick={this.toggleShow}>
            Toggle All {this.state.open ? "Closed" : "Open"}
          </button>
        </GridItem>
        <GridItem columnSpan={this.overview ? 9 : 12}>
          <ListErrors
            accountId={this.accountId}
            query={querySelect}
            open={this.state.open}
            scrollable={this.scrollable}
          />
        </GridItem>
        {this.overview && (
          <GridItem columnSpan={3}>
            <BillboardChart
              style={{ height: "100px" }}
              accountId={this.accountId}
              query={queryCount}
            />
            <StackedBarChart
              style={{ height: "200px" }}
              accountId={this.accountId}
              query={queryBarClass}
            />
          </GridItem>
        )}
      </Grid>
    );
  }
}
