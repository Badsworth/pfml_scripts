import React, { useState } from "react";
import PropTypes from "prop-types";
import useUniqueId from "../hooks/useUniqueId";

/**
 * An accordion is a list of headers that hide or reveal additional content when selected.
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/accordion/)
 */
function AccordionItem(props) {
  const id = useUniqueId("accordion");
  const [isExpanded, setExpanded] = useState(false);

  function handleClick() {
    setExpanded(!isExpanded);
  }

  return (
    <React.Fragment>
      <h2 className="usa-accordion__heading">
        <button
          className="usa-accordion__button"
          aria-expanded={isExpanded}
          aria-controls={id}
          onClick={handleClick}
          type="button"
        >
          {props.heading}
        </button>
      </h2>
      <div
        id={id}
        data-testid={id}
        className="usa-accordion__content usa-prose"
        hidden={!isExpanded}
      >
        {props.children}
      </div>
    </React.Fragment>
  );
}

AccordionItem.propTypes = {
  children: PropTypes.node.isRequired,
  heading: PropTypes.string.isRequired,
};

export default AccordionItem;
