import PropTypes from "prop-types";
import React from "react";

/**
 * An accordion is a list of headers that hide or reveal additional content when selected.
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/accordion/)
 */
function Accordion(props) {
  return (
    <div
      className="usa-accordion usa-accordion--bordered"
      aria-multiselectable="true"
    >
      {props.children}
    </div>
  );
}

Accordion.propTypes = {
  /**
   * One or more `AccordionItem` elements
   */
  children: PropTypes.node.isRequired,
};

export default Accordion;
