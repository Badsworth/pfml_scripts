import React from "react";
import classnames from "classnames";

interface FieldsetProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Thin wrapper around a fieldset element to normalize how
 * child margins are rendered
 */
const Fieldset = (props: FieldsetProps) => {
  // Add a top margin because the Legend's margin gets collapsed:
  // https://github.com/uswds/uswds/issues/4153
  const classNames = classnames("usa-fieldset margin-top-3", props.className);
  return <fieldset className={classNames}>{props.children}</fieldset>;
};

export default Fieldset;
