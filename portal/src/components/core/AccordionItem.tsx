import React, { useState } from "react";
import classnames from "classnames";
import useUniqueId from "../../hooks/useUniqueId";

interface AccordionItemProps {
  children: React.ReactNode;
  className?: string;
  heading: string;
}

/**
 * An accordion is a list of headers that hide or reveal additional content when selected.
 * [USWDS Reference ↗](https://designsystem.digital.gov/components/accordion/)
 */
function AccordionItem(props: AccordionItemProps) {
  const id = useUniqueId("accordion");
  const [isExpanded, setExpanded] = useState(false);

  const handleClick = () => {
    setExpanded(!isExpanded);
  };

  return (
    <React.Fragment>
      <h2 className={classnames("usa-accordion__heading", props.className)}>
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

export default AccordionItem;
