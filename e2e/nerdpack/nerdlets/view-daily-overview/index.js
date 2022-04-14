import React from "react";
import Navigation from "../common/components/Navigation";
import { PlatformStateContext } from "nr1";
import { format as dateFormat } from "date-fns";
import { DAO } from "../common/DAO";
import { FilterByEnv, FilterByTagGroup } from "../common/components/Filters";
import { EnvironmentsOverviewTable } from "../common/components/EnvironmentsOverviewTable";
import { MorningReport } from "../common/components/MorningReport";

export default class ViewDailyOverviewNerdlet extends React.Component {
  state = {
    envWhere: "",
    env: [],
    tagWhere: "",
    tags: [],
  };

  handleUpdateEnv = (nrql, envObject, envArray) => {
    this.setState({ envWhere: nrql, env: envArray });
  };

  handleUpdateTag = (nrql, tagObject, tagArray) => {
    this.setState({ tagWhere: nrql, tags: tagArray });
  };

  getFilters = () => {
    const env = this.getFiltersEnv();
    const tag = this.getFiltersTags();
    if (env != "" && tag != "") {
      return `(${env} AND ${tag})`;
    }
    return `${env}${tag}`;
  };

  getFiltersEnv = () => {
    return this.state.envWhere;
  };

  getEnvsArray = () => {
    return this.state.env;
  };

  getFiltersTags = () => {
    if (this.state.tagWhere) {
      return `(group = 'Integration' AND tagGroup = '') OR (group != 'Integration' AND  ${this.state.tagWhere})`;
    }
    return "";
  };

  render() {
    var now = new Date(); // now

    now.setHours(0); // set hours to 0
    now.setMinutes(0); // set minutes to 0
    now.setSeconds(0); // set seconds to 0

    var startOfDay = Math.floor(now / 1000);

    now.setHours(23); // set hours to 0
    now.setMinutes(59); // set minutes to 0
    now.setSeconds(59); // set seconds to 0

    var endOfDay = Math.floor(now / 1000);

    const since = `${startOfDay} UNTIL ${endOfDay}`;
    return [
      <Navigation active="view-daily-overview" />,
      <h2>Runs for {dateFormat(now, "MM/dd/yyyy")}</h2>,
      <FilterByEnv
        handleUpdate={this.handleUpdateEnv}
        returnType={FilterByEnv.RETURN_TYPES.ALL}
      />,
      <FilterByTagGroup
        handleUpdate={this.handleUpdateTag}
        returnType={FilterByEnv.RETURN_TYPES.ALL}
      />,
      <PlatformStateContext.Consumer>
        {(platformState) => {
          DAO.ACCOUNT_ID = platformState.accountId;
          return [
            <EnvironmentsOverviewTable
              accountId={platformState.accountId}
              since={since}
              where={this.getFiltersTags()}
              envs={this.state.env}
              limitRuns={"max"}
              simpleView={false}
            />,
            <MorningReport
              since={since}
              where={this.state.tagWhere}
              envs={this.state.env}
            />,
          ];
        }}
      </PlatformStateContext.Consumer>,
    ];
  }
}
