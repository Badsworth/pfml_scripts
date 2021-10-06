import React from "react";
import {
  PlatformStateContext,
  Grid,
  GridItem,
  HeadingText,
  AreaChart,
  TableChart,
  BillboardChart,
  LineChart,
  NrqlQuery,
} from "nr1";
// https://docs.newrelic.com/docs/new-relic-programmable-platform-introduction

export default class GridNerdlet extends React.Component {
  constructor(props) {
    super(props);
    this.accountId = "2837112";
  }
  render() {
    const avgResTime = `SELECT average(duration) FROM Transaction FACET appName TIMESERIES AUTO `;
    const trxOverview = `FROM Transaction SELECT count(*) as 'Transactions', apdex(duration) as 'apdex', percentile(duration, 99, 95) FACET appName `;
    const latestRuns =
      "SELECT count(*) FROM CypressTestResult WHERE environment LIKE 'test%' AND (tag LIKE 'Morning run%' OR tag LIKE 'Deploy%') FACET runId, file SINCE today";

    return (
      <PlatformStateContext.Consumer>
        {(PlatformState) => {
          const since = "SINCE today";

          return (
            <>
              <Grid
                className="primary-grid"
                spacingType={[Grid.SPACING_TYPE.NONE, Grid.SPACING_TYPE.NONE]}
              >
                <GridItem className="primary-content-container" columnSpan={6}>
                  <main className="primary-content full-height">
                    <HeadingText
                      spacingType={[HeadingText.SPACING_TYPE.MEDIUM]}
                      type={HeadingText.TYPE.HEADING_4}
                    >
                      Transaction Overview
                    </HeadingText>
                    <TableChart
                      fullWidth
                      accountId={this.accountId}
                      query={trxOverview + since}
                    />
                  </main>
                </GridItem>
                <GridItem className="primary-content-container" columnSpan={6}>
                  <main className="primary-content full-height">
                    <HeadingText
                      spacingType={[HeadingText.SPACING_TYPE.MEDIUM]}
                      type={HeadingText.TYPE.HEADING_4}
                    >
                      Average Response Time
                    </HeadingText>
                    <AreaChart
                      fullWidth
                      accountId={this.accountId}
                      query={avgResTime + since}
                    />
                  </main>
                </GridItem>
                <GridItem columnSpan={12}></GridItem>
              </Grid>
              <NrqlQuery accountId={this.accountId} query={latestRuns}>
                {(res) => {
                  console.log(res);
                  return (
                    <pre>{JSON.stringify(res.data?.[0]?.data, null, 2)}</pre>
                  );
                }}
              </NrqlQuery>
            </>
          );
        }}
      </PlatformStateContext.Consumer>
    );
  }
}
