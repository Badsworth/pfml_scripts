import React from "react";
import { NerdletStateContext, PlatformStateContext } from "nr1";
import EnvTimelineWidget from "./EnvTimeline";
import { DAO } from "../common/DAO";

// https://docs.newrelic.com/docs/new-relic-programmable-platform-introduction

export default class PFMLDeploymentsNerdlet extends React.PureComponent {
  render() {
    return (
      <PlatformStateContext.Consumer>
        {(platformState) => (
          <NerdletStateContext.Consumer>
            {(nerdletState) => {
              // State is how we receive our routing metadata.
              DAO.ACCOUNT_ID = platformState.accountId;
              return (
                <EnvTimelineWidget
                  environment={nerdletState.environment}
                  component={nerdletState.component}
                />
              );
            }}
          </NerdletStateContext.Consumer>
        )}
      </PlatformStateContext.Consumer>
    );
  }
}
