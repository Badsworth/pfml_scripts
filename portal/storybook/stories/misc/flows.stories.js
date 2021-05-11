import { pick, pickBy } from "lodash";
import FlowDiagram from "../../utils/FlowDiagram";
import React from "react";
import Step from "src/models/Step";
import auth from "src/flows/auth";
import claimant from "src/flows/claimant";
import employer from "src/flows/employer";
import machineConfig from "src/flows";
import routes from "src/routes";

export default {
  title: "Misc/Flows",
};

export const Intro = () => {
  return (
    <p>The diagrams below represent the routing logic currently implemented.</p>
  );
};

export const Auth = () => <FlowDiagram states={auth.states} />;

export const Employer = () => <FlowDiagram states={employer.states} />;

export const ClaimantChecklistAndReview = () => (
  <React.Fragment>
    <FlowDiagram
      states={pick(claimant.states, [routes.applications.checklist])}
    />
    <FlowDiagram states={pick(claimant.states, [routes.applications.review])} />
  </React.Fragment>
);

export const ClaimantSteps = () => (
  <FlowDiagram
    states={pickBy(claimant.states, (s) => s.meta && s.meta.step)}
    maxWidth="200%"
  />
);

export const ClaimantFields = () => {
  const steps = Step.createClaimStepsFromMachine(machineConfig, { claim: {} });

  return steps.map((step) => {
    return (
      <section key={step.name}>
        <h2>{step.name}</h2>
        {step.pages.map((page) => {
          return (
            <article key={page.route}>
              <h3>{page.route}</h3>
              <ul>
                {page.meta.fields.map((field) => (
                  <li key={field}>
                    <code>{field}</code>
                  </li>
                ))}
              </ul>
            </article>
          );
        })}
        <hr />
      </section>
    );
  });
};
