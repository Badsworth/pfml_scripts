import React from "react";
import { PlatformStateContext } from "nr1";
import { EnvironmentsOverviewTable } from "../common/components/EnvironmentsOverviewTable";
import Navigation from "../common/components/Navigation";
import { DAO } from "../common/DAO";

export default class PFMLEnvironmentsNerdlet extends React.PureComponent {
  render() {
    const where = `(tag LIKE '%Morning Run%'
                    OR tag LIKE 'Deploy%'
                    OR (tag LIKE 'Manual%' AND branch = 'main')) AND group = 'Commit Stable'`;
    return (
      <PlatformStateContext.Consumer>
        {(platformState) => {
          DAO.ACCOUNT_ID = platformState.accountId;
          return [
            <Navigation active="view-environment-overview" />,
            <EnvironmentsOverviewTable
              accountId={platformState.accountId}
              where={where}
            />,
          ];
        }}
      </PlatformStateContext.Consumer>
    );
  }
}
