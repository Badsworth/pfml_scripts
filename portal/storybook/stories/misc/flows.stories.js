import React from "react";
import Step from "src/models/Step";
import auth from "src/flows/auth";
import claimant from "src/flows/claimant";
import employer from "src/flows/employer";
import machineConfig from "src/flows";
import { stateMachineToSvg } from "./stateMachineToSvg";
import { uniqueId } from "lodash";

export default {
  title: "Misc/Flows",
};

export const Intro = () => {
  return (
    <p>The diagrams below represent the routing logic currently implemented.</p>
  );
};

/**
 * Convert the XState representation of our flow into
 * State Machine cat (smcat) syntax and resulting state chart
 * @see https://github.com/sverweij/state-machine-cat
 * @see https://state-machine-cat.js.org/
 * @returns {React.Component}
 */
const FlowDiagram = (props) => {
  const svg = stateMachineToSvg(props.states);
  const maxWidth = props.maxWidth || "100%";
  const id = uniqueId("flow");

  return (
    <React.Fragment>
      <style>{`#${id} svg { height: auto; max-width: ${maxWidth} }`}</style>
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

export const Auth = () => <FlowDiagram states={auth} />;
export const Employer = () => <FlowDiagram states={employer} />;
export const Claimant = () => <FlowDiagram states={claimant} maxWidth="200%" />;

export const ClaimFlowFields = () => {
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
