import { get } from "lodash";
import smcat from "state-machine-cat";

/**
 * Convert a state machine to an SVG state chart.
 * @param {object} machineConfig
 * @param {{initial: string, meta: object, on: string|Array[]}} machineConfig.states
 * @returns {string} SVG markup
 */
export function stateMachineToSvg(machineConfig) {
  const smcatString = stateMachineToSmcat(machineConfig);
  const svg = smcat.render(smcatString, {
    outputType: "svg",
  });

  return svg;
}

/**
 * Convert a state machine to a smcat syntax.
 * smcat is a markup language for state machines.
 * We first convert our state machine to smcat,
 * so that we can then use the library to export
 * it as an SVG
 * @see https://github.com/sverweij/state-machine-cat
 * @param {object} machineConfig
 * @param {{initial: string, meta: object, on: string|Array[]}} machineConfig.states
 * @returns {string} SVG markup
 */
export function stateMachineToSmcat(machineConfig) {
  let smcatOutput = [];
  const states = machineConfig.states;
  const groups = {};

  // Create hierarchical state nodes, grouping by the meta.step attribute on each state node
  for (const route in states) {
    const node = states[route];
    const groupName = get(node, "meta.step") || "_root";
    // create group if it doesn't already exist
    groups[groupName] = groups[groupName] || {};
    // Add the node to the group
    groups[groupName][route] = node;
  }

  // smcat requires root nodes (nodes without a parent) to be output
  // slightly differently, so we need to separate them from nested nodes
  const { _root, ...steps } = groups;

  // Since we're outputting a nested state machine, our root nodes
  // need defined at the top of the smcat first, before we output
  // any transitions to them
  for (const route in _root) {
    smcatOutput.push(`"${route}",`); // Outputs: "/routeA",
  }

  // We need a way to identify whether we've reached the last step
  // so that we can use the correct delimiter in smcat output
  const totalSteps = Object.keys(steps).length;
  let delimiterCounter = 0;

  // Output each nested state machine
  for (const stepName in steps) {
    delimiterCounter++;
    const states = steps[stepName];

    // Start nested state node grouping
    smcatOutput.push(`${stepName} {`); // Outputs:  stepA {

    // Add a transition for every node
    smcatOutput = smcatOutput.concat(smcatTransitionGroup(states));

    // Last nested state machine needs a semi-colon
    const delimiter = delimiterCounter < totalSteps ? "," : ";";

    // Close nested state machine
    smcatOutput.push(`}${delimiter}`); // Outputs:  },
  }

  // After all of the nested state nodes, output transitions for every top-level state node
  smcatOutput = smcatOutput.concat(smcatTransitionGroup(_root));

  const smcatString = smcatOutput.join("\n\n"); // adding line breaks for readability

  // You can copy and paste the smcat output into https://state-machine-cat.js.org
  // eslint-disable-next-line no-console
  console.log(smcatString);

  return smcatString;
}

/**
 * Generate smcat syntax for a collection of state nodes
 * @param {object[]} states
 * @returns {string[]} smcat transitions
 */
function smcatTransitionGroup(states) {
  const smcatOutput = [];

  for (const route in states) {
    const node = states[route];
    const events = node.on;

    for (const eventName in events) {
      const action = events[eventName];

      if (typeof action === "string") {
        const nextRoute = action;
        smcatOutput.push(smcatTransition(route, nextRoute, eventName));
        continue;
      }

      // Conditional routes
      action.forEach((conditionalAction) => {
        const nextRoute = conditionalAction.target;
        const condition = conditionalAction.cond;

        if (condition) {
          return smcatOutput.push(
            smcatTransition(route, nextRoute, eventName, condition)
          );
        }

        smcatOutput.push(smcatTransition(route, nextRoute, eventName));
      });
    }
  }

  return smcatOutput;
}

/**
 * Generate smcat syntax for a transition between one state to the next
 * @param {string} from
 * @param {string} to
 * @param {string} event
 * @param {string} [condition]
 * @returns {string}
 */
function smcatTransition(from, to, event, condition) {
  let output = `"${from}" => "${to}": ${event}`;
  if (condition) output += ` [${condition}]`;

  // Example output: `"/page-a" => "/page-b": CONTINUE [answeredYes]`
  return `${output};`;
}
