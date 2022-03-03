import React from "react";
import TestGrid from "./TestGrid";
import { PlatformStateContext, NerdletStateContext } from "nr1";
import { DAO } from "../common/DAO";

// https://docs.newrelic.com/docs/new-relic-programmable-platform-introduction

export default class PFMLE2ETestGridNerdlet extends React.Component {
  render() {
    return (
      <PlatformStateContext.Consumer>
        {(platformState) => (
          <NerdletStateContext.Consumer>
            {(
              nerdletState // State is how we receive our routing metadata.
            ) => {
              DAO.ACCOUNT_ID = platformState.accountId;
              return <TestGrid runIds={nerdletState.runIds} />;
            }}
          </NerdletStateContext.Consumer>
        )}
      </PlatformStateContext.Consumer>
    );
  }
}
