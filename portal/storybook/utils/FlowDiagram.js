import React, { useEffect, useState } from "react";
import { camelCase, get, uniqueId } from "lodash";
import PropTypes from "prop-types";
import mermaid from "mermaid";

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

FlowDiagram.propTypes = {
  direction: PropTypes.oneOf(["TB", "LR"]),
  maxWidth: PropTypes.string,
  states: PropTypes.object.isRequired,
};

export default FlowDiagram;

// Hopefully enough colors to cover the number of potential state node groups
const fills = [
  "#c5ee93",
  "#ffe396",
  "#83fcd4",
  "#7efbe1",
  "#a8f2ff",
  "#cfe8ff",
  "#e0e0ff",
  "#ede3ff",
  "#ffddea",
  "#ffddea",
  "#fdb8ae",
];

/**
 * Convert a state machine to an SVG state chart.
 * @param {Array<{meta: object, on: string|Array[]}>} states
 * @param {object} options
 * @param {'TB'|'LR'} options.direction
 * @returns {string} SVG markup
 */
export function stateMachineToSvg(states, options = {}) {
  mermaid.mermaidAPI.initialize({
    startOnLoad: false,
    securityLevel: "loose", // allow HTML tags
  });

  const graphDefinition = stateMachineToMermaid(states, options);

  return new Promise((resolve) => {
    mermaid.mermaidAPI.render("graphDiv", graphDefinition, (svg) =>
      resolve(svg)
    );
  });
}

/**
 * Convert a state machine to Mermaid flowchart syntax.
 * We first convert our state machine to Mermaid,
 * so that we can then use the library to export
 * it as an SVG
 * @see https://mermaid-js.github.io/mermaid/#/flowchart
 * @param {Array<{meta: object, on: string|Array[]}>} states
 * @param {object} options
 * @param {'TB'|'LR'} options.direction
 * @returns {string} Mermaid graph definition
 */
export function stateMachineToMermaid(states, options) {
  let mermaidOutput = [`flowchart ${options.direction}\n`];
  const groups = {};
  let fillIndex = 0;

  // Create hierarchical state nodes, grouping by the meta.step attribute on each state node
  for (const route in states) {
    const node = states[route];
    const groupName = get(node, "meta.step") || "_root";
    // create group if it doesn't already exist
    groups[groupName] = groups[groupName] || {};
    // Add the node to the group
    groups[groupName][route] = node;
  }

  // Separate out root nodes (nodes without a parent) to be output
  const { _root, ...steps } = groups;

  if (_root) {
    mermaidOutput = mermaidOutput.concat(
      mermaidTransitionGroup(_root, fills[fillIndex])
    );
  }

  // Output each nested state machine
  for (const stepName in steps) {
    fillIndex++;
    const states = steps[stepName];

    // Add a transition for every node
    mermaidOutput = mermaidOutput.concat(
      mermaidTransitionGroup(states, fills[fillIndex])
    );
  }

  // adding line breaks for readability
  const mermaidString = mermaidOutput.join("\n\n");

  return mermaidString;
}

/**
 * Generate Mermaid syntax for a collection of state nodes
 * @param {object[]} states
 * @param {string} fill - HEX color
 * @returns {string[]} Mermaid transitions
 */
function mermaidTransitionGroup(states, fill) {
  const mermaidOutput = [];

  for (const route in states) {
    const node = states[route];
    // Our state nodes currently have one or the other, but not both. It's either a transient state or not.
    const events = node.always ? { "*": true } : node.on;

    for (const eventName in events) {
      const action = eventName === "*" ? node.always : events[eventName];

      if (typeof action === "string") {
        const nextRoute = action;
        mermaidOutput.push(
          mermaidTransition(fill, route, nextRoute, eventName)
        );
        continue;
      }

      // Conditional routes
      action.forEach((conditionalAction, index) => {
        const nextRoute = conditionalAction.target;
        const condition = conditionalAction.cond;

        if (condition) {
          return mermaidOutput.push(
            mermaidTransition(
              fill,
              route,
              nextRoute,
              eventName,
              `[${index + 1}] ${condition}`
            )
          );
        }

        mermaidOutput.push(
          mermaidTransition(fill, route, nextRoute, eventName)
        );
      });
    }
  }

  return mermaidOutput;
}

/**
 * Generate Mermaid flowchart syntax for a transition between one state to the next
 * @param {string} fill - HEX color
 * @param {string} from
 * @param {string} to
 * @param {string} event
 * @param {string} [condition]
 * @returns {string}
 */
function mermaidTransition(fill, from, to, event, condition) {
  event = condition ? `"${event}\n${condition}"` : event;

  // Use dotted arrows for specific transitions
  const arrow = to === "/applications/checklist" ? "-.->" : "-->";
  const fromId = camelCase(from);
  const toId = camelCase(to);

  // Mermaid doesn't support slashes in the node IDs, so we call camelCase on those
  // Example output: login["/login"] --> |CONTINUE| dashboard["/dashboard"]
  return [
    `${fromId}["${from}"] ${arrow} |${event}| ${toId}["${to}"]`,
    `style ${fromId} fill:${fill},stroke:transparent`,
    `style ${toId} fill:${fill},stroke:transparent`,
  ].join("\n");
}
