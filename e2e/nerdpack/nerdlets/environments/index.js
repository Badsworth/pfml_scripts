import React from "react";
import { PlatformStateContext } from "nr1";
import { EnvironmentsTable } from "../common/components/EnvironmentsTable";
import Navigation from "../common/components/Navigation";
// https://docs.newrelic.com/docs/new-relic-programmable-platform-introduction

export default class PFMLEnvironmentsNerdlet extends React.PureComponent {
  render() {
    const where = `(tag LIKE '%Morning Run%'
                    OR tag LIKE 'Deploy%'
                    OR (tag LIKE 'Manual%' AND branch = 'main')) AND group = 'Commit Stable'`;
    return (
      <PlatformStateContext.Consumer>
        {(platformState) => [
          <Navigation active="environment-v1" />,
          <EnvironmentsTable
            accountId={platformState.accountId}
            where={where}
          />,
        ]}
      </PlatformStateContext.Consumer>
    );
  }
}
