import React, { useEffect, useState } from "react";
import { pick, pickBy, uniqueId } from "lodash";
import Step from "src/models/Step";
import auth from "src/flows/auth";
import claimant from "src/flows/claimant";
import employer from "src/flows/employer";
import machineConfig from "src/flows";
import routes from "src/routes";
import { stateMachineToSvg } from "./stateMachineToSvg";

export default {
  title: "Misc/Flows",
};

export const Intro = () => {
  return (
    <p>The diagrams below represent the routing logic currently implemented.</p>
  );
};

/**
 * Convert the XState representation of our flow into an SVG flowchart
 * @returns {React.Component}
 */
const FlowDiagram = ({ direction = "TB", ...props }) => {
  const { states } = props;
  const maxWidth = props.maxWidth || "100%";
  const id = uniqueId("flow");

  const [svg, setSvg] = useState();
  useEffect(() => {
    stateMachineToSvg(states, { direction })
      .then((svgOutput) => {
        setSvg(svgOutput);
      })
      .catch(console.error);
  }, [direction, states, setSvg]);

  if (!svg) return <p>Loading</p>;

  return (
    <React.Fragment>
      <style>{`#${id} svg { height: auto; width: auto; max-width: ${maxWidth} !important; }`}</style>
      <div
        id={id}
        style={{
          border: "1px solid #eee",
          overflow: "auto",
        }}
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </React.Fragment>
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
