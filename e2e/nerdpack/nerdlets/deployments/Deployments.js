import { EmptyState, NrqlQuery } from "nr1";
import { Timeline } from "@newrelic/nr1-community";
import React from "react";
import { labelComponent } from "../common";

export default function DeploymentsWidget({
  environment,
  component,
  accountId,
}) {
  const where = [];
  if (environment) {
    where.push(`environment = '${environment}'`);
  }
  if (component) {
    where.push(`component = '${component}'`);
  }
  const query = `SELECT version, component, timestamp FROM CustomDeploymentMarker ${
    where.length ? `WHERE ${where.join(" AND ")}` : ""
  } SINCE 3 months ago LIMIT 20`;
  return (
    <NrqlQuery query={query} accountId={accountId}>
      {({ data }) => {
        const rows = (data?.[0]?.data ?? []).map((row) => {
          const component = labelComponent(row.component);
          return {
            ...row,
            label: `${component} Deployment: ${row.version}`,
          };
        });
        if (rows.length) {
          return <Timeline data={rows} labelField={"label"} />;
        }
        return (
          <EmptyState
            title={"No Deployments Found"}
            description={"No deployments were recorded during this time range."}
          />
        );
      }}
    </NrqlQuery>
  );
}
