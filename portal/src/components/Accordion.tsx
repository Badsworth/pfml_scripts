import React from "react";

interface AccordionProps {
  children: React.ReactNode;
}

/**
 * An accordion is a list of headers that hide or reveal additional content when selected.
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/accordion/)
 */
function Accordion(props: AccordionProps) {
  return (
    <div
      className="usa-accordion usa-accordion--bordered"
      aria-multiselectable="true"
    >
      {props.children}
    </div>
  );
}

export default Accordion;
