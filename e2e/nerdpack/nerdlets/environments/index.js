import React from "react";
import { PlatformStateContext } from "nr1";
import EnvironmentsTable from "./EnvironmentsTable";

// https://docs.newrelic.com/docs/new-relic-programmable-platform-introduction

export default class PFMLEnvironmentsNerdlet extends React.PureComponent {
  render() {
    return (
      <PlatformStateContext.Consumer>
        {(platformState) => <EnvironmentsTable platformState={platformState} />}
      </PlatformStateContext.Consumer>
    );
  }
}
