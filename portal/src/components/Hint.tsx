import React from "react";
import classnames from "classnames";

interface HintProps {
  /**
   * Additional classes for hint
   */
  className?: string;
  /**
   * Enable the smaller variant, which is used when the field is
   * already accompanied by larger question text (like a legend).
   * Defaults to false
   */
  small?: boolean;
  /**
   * For hints related to an input, the ID of the field this hint is for.
   */
  inputId?: string;
  /**
   * Localized hint text
   */
  children: React.ReactNode;
}

const Hint = (props: HintProps) => {
  const hintClasses = classnames(
    `display-block line-height-sans-5 measure-5`,
    props.className,
    {
      // Use hint styling for small labels
      "usa-hint text-base-darkest": props.small,
      // Use lead styling for regular labels
      "usa-intro": !props.small,
    }
  );
  const id = props.inputId ? `${props.inputId}_hint` : undefined;

  return (
    <span className={hintClasses} id={id}>
      {props.children}
    </span>
  );
};

export default Hint;
