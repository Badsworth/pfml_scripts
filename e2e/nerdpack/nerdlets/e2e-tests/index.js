import React from "react";
import TestGrid from "./TestGrid";
import { PlatformStateContext, NerdletStateContext } from "nr1";

// https://docs.newrelic.com/docs/new-relic-programmable-platform-introduction

export default class PFMLE2ETestsNerdlet extends React.Component {
  render() {
    return (
      <PlatformStateContext.Consumer>
        {(platformState) => (
          <NerdletStateContext.Consumer>
            {(
              nerdletState // State is how we receive our routing metadata.
            ) => (
              <TestGrid
                accountId={platformState.accountId}
                environment={nerdletState.environment}
                runIds={nerdletState.runIds}
              />
            )}
          </NerdletStateContext.Consumer>
        )}
      </PlatformStateContext.Consumer>
    );
  }
}
