import { stateMachineToSmcat, stateMachineToSvg } from "./stateMachineToSvg";
import React from "react";
import Step from "src/models/Step";
import machineConfig from "src/routes/claim-flow-configs";

export default {
  title: "Flows/Claim",
};

/**
 * Convert the XState representation of our flow into
 * State Machine cat (smcat) syntax and resulting state chart
 * @see https://github.com/sverweij/state-machine-cat
 * @see https://state-machine-cat.js.org/
 * @returns {React.Component}
 */
export const Default = () => {
  return (
    <React.Fragment>
      <style>{`svg { height: auto; max-width: 100% }`}</style>
      <p style={{ fontSize: 12, marginTop: 0, marginBottom: 30 }}>
        The diagram below represents the routing logic currently implemented.
        You can open this preview in a new tab, by clicking the up arrow icon in
        the toolbar above, to view this in a larger window.
      </p>
      <div
        dangerouslySetInnerHTML={{ __html: stateMachineToSvg(machineConfig) }}
      />
    </React.Fragment>
  );
};

export const Smcat = () => {
  return (
    <React.Fragment>
      <p>
        smcat stands for{" "}
        <a href="https://github.com/sverweij/state-machine-cat">
          state machine cat
        </a>{" "}
        and is a shorthand syntax for writing{" "}
        <a href="https://statecharts.github.io/">statecharts</a>. Mainly, it
        helps us generate a somewhat legible statechart (shown above), so we're
        using it until we find a better library for generating statecharts. You
        can copy the text below and paste it into the{" "}
        <a href="https://state-machine-cat.js.org/">smcat visualizer</a> to play
        around with the diagram.
      </p>

      <pre style={{ fontSize: 11, padding: 20, border: "1px solid #999" }}>
        {stateMachineToSmcat(machineConfig)}
      </pre>
    </React.Fragment>
  );
};

export const ClaimFlowFields = () => {
  const steps = Step.createClaimStepsFromMachine(machineConfig);

  return steps.map((step) => {
    return (
      <section key={step.name}>
        <h2>{step.name}</h2>
        {step.pages.map((page) => {
          return (
            <article key={page.route}>
              <h3>{page.route}</h3>
              <ul>
                {page.fields.map((field) => (
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
