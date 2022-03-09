import React from "react";
import Navigation from "../common/components/Navigation";
import {
  BillboardChart,
  StackedBarChart,
  AreaChart,
  PieChart,
  GridItem,
  Grid,
  ChartGroup,
  PlatformStateContext,
} from "nr1";
import { timeRangeToNrql } from "@newrelic/nr1-community";
import { labelEnv } from "../common";
import { getCategoriesByPriority } from "../common/ErrorPriority";
import { ListErrors } from "../common/components/ListErrors";

class UncategorizedList extends React.Component {
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
  }

  toggleShow = () => {
    this.setState((state) => ({ open: !state.open }));
  };

  render() {
    const query = `FROM CypressTestResult
                         WHERE pass is false
                           and category is null ${
                             this.state.where ? "AND" : ""
                           } ${this.state.where} ${this.state.since}`;
    const querySelect = `SELECT * ${query}`;
    const queryCount = `SELECT count(*) as Total ${query}`;
    const queryBarClass = `SELECT count(*) as Total ${query} FACET errorClass`;
    return (
      <Grid className={"E2E-error-list"}>
        <GridItem className={"ListHeader"} columnSpan={12}>
          <h1>Uncategorized Errors</h1>
          <button onClick={this.toggleShow}>
            Toggle All {this.state.open ? "Closed" : "Open"}
          </button>
        </GridItem>
        <GridItem columnSpan={9}>
          <ListErrors
            accountId={this.accountId}
            query={querySelect}
            open={this.state.open}
          ></ListErrors>
        </GridItem>
        <GridItem columnSpan={3}>
          <BillboardChart
            style={{ height: "100px" }}
            accountId={this.accountId}
            query={queryCount}
          ></BillboardChart>
          <StackedBarChart
            style={{ height: "200px" }}
            accountId={this.accountId}
            query={queryBarClass}
          ></StackedBarChart>
        </GridItem>
      </Grid>
    );
  }
}

class PriorityList extends React.Component {
  state = {
    since: "",
    where: "",
    open: false,
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
    this.priority = props.priority;
  }

  toggleShow = () => {
    this.setState((state) => ({ open: !state.open }));
  };

  render() {
    const catList = getCategoriesByPriority(this.priority);
    const catWhere = catList
      .map((item) => {
        return (
          "(" +
          Object.keys(item)
            .map((key) => {
              return `${key} = '${item[key]}'`;
            })
            .join(" AND ") +
          ")"
        );
      })
      .join(" OR ");

    const query = `FROM CypressTestResult
                         WHERE pass is false
                           ${this.state.where ? "AND" : ""} ${this.state.where}
                           AND ( ${catWhere} )
                           ${this.state.since}`;
    const querySelect = `SELECT * ${query}`;
    const queryCount = `SELECT count(*) as Total ${query}`;
    const queryBarClass = `SELECT count(*) as Total ${query} FACET category, subCategory`;

    return (
      <Grid className={"E2E-error-list"}>
        <GridItem className={"ListHeader"} columnSpan={12}>
          <h1>{this.priority} Errors</h1>
          <button onClick={this.toggleShow}>
            Toggle All {this.state.open ? "Closed" : "Open"}
          </button>
        </GridItem>
        <GridItem columnSpan={9}>
          <ListErrors
            accountId={this.accountId}
            query={querySelect}
            open={this.state.open}
          ></ListErrors>
        </GridItem>
        <GridItem columnSpan={3}>
          <BillboardChart
            style={{ height: "100px" }}
            accountId={this.accountId}
            query={queryCount}
          ></BillboardChart>
          <StackedBarChart
            style={{ height: "200px" }}
            accountId={this.accountId}
            query={queryBarClass}
          ></StackedBarChart>
        </GridItem>
      </Grid>
    );
  }
}

export default class CategoriesNerdlet extends React.Component {
  state = {
    env: {
      breakfix: true,
      training: true,
      uat: true,
      performance: true,
      stage: true,
      "cps-preview": true,
      test: true,
    },
  };

  clearAll = () => {
    const state = { ...this.state.env };
    Object.keys(state).map((env) => {
      state[env] = false;
    });
    this.setState({
      env: state,
    });
  };

  checkAll = () => {
    const state = { ...this.state.env };
    Object.keys(state).map((env) => {
      state[env] = true;
    });
    this.setState({
      env: state,
    });
  };

  handleInputChange = (event) => {
    const target = event.target;
    const value = target.type === "checkbox" ? target.checked : target.value;
    const name = target.name;

    const state = { ...this.state.env, [name]: value };
    this.setState({
      env: state,
    });
  };

  getFilters = () => {
    let WHERE = [];
    Object.keys(this.state.env).map((env) => {
      if (this.state.env[env]) {
        WHERE.push(`environment = '${env}'`);
      }
    });
    if (WHERE.length) {
      return `( ${WHERE.join(" OR ")} )`;
    }
    return "";
  };

  getTimelineCat = (where, since) => {
    return `SELECT count(*) as Errors
                FROM CypressTestResult
                WHERE pass is false
                ${where ? "AND" : ""} ${where}
                ${since}
                TIMESERIES day`;
  };

  getPieQueryCat = (where, since) => {
    return `SELECT count(*)
                FROM CypressTestResult
                WHERE pass is false
                ${where ? "AND" : ""} ${where}
                FACET category
                ${since}`;
  };
  getPieQuerySubCat = (where, since) => {
    return `SELECT count(*)
                FROM CypressTestResult
                WHERE pass is false
                ${where ? "AND" : ""} ${where}
                FACET category, subCategory
                ${since}`;
  };

  render() {
    const where = this.getFilters();
    return [
      <Navigation active="error-v1"></Navigation>,
      <div className={"filters"}>
        FILTERS:
        <button onClick={this.clearAll}>Clear All</button>
        <button onClick={this.checkAll}>Check All</button>
        {Object.keys(this.state.env).map((status) => {
          return (
            <label>
              <input
                name={status}
                type={"checkbox"}
                checked={this.state.env[status]}
                onChange={this.handleInputChange}
              />
              {labelEnv(status)}
            </label>
          );
        })}
      </div>,
      <PlatformStateContext.Consumer>
        {(platformState) => {
          const since = timeRangeToNrql(platformState);
          return [
            <ChartGroup>
              <Grid className={"E2E-error-list"}>
                <GridItem className={"ListHeader"} columnSpan={12}>
                  <h1>Category Summary</h1>
                </GridItem>
                <GridItem columnSpan={6}>
                  <PieChart
                    accountId={platformState.accountId}
                    query={this.getPieQueryCat(where, since)}
                    fullWidth
                  ></PieChart>
                </GridItem>
                <GridItem columnSpan={6}>
                  <PieChart
                    accountId={platformState.accountId}
                    query={this.getPieQuerySubCat(where, since)}
                    fullWidth
                  ></PieChart>
                </GridItem>
                <GridItem columnSpan={12}>
                  <AreaChart
                    accountId={platformState.accountId}
                    query={this.getTimelineCat(where, since)}
                    fullWidth
                  ></AreaChart>
                </GridItem>
              </Grid>
            </ChartGroup>,
            <UncategorizedList
              accountId={platformState.accountId}
              since={since}
              where={where}
            ></UncategorizedList>,
            <PriorityList
              accountId={platformState.accountId}
              since={since}
              where={where}
              priority={"EDM"}
            ></PriorityList>,
            <PriorityList
              accountId={platformState.accountId}
              since={since}
              where={where}
              priority={"HIGH"}
            ></PriorityList>,
            <PriorityList
              accountId={platformState.accountId}
              since={since}
              where={where}
              priority={"MEDIUM"}
            ></PriorityList>,
            <PriorityList
              accountId={platformState.accountId}
              since={since}
              where={where}
              priority={"LOW"}
            ></PriorityList>,
          ];
        }}
      </PlatformStateContext.Consumer>,
    ];
  }
}
