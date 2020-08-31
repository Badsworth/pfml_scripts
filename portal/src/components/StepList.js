import React, { Children, cloneElement } from "react";
import Heading from "./Heading";
import PropTypes from "prop-types";
import Step from "./Step";

const StepList = (props) => {
  const { children, description, offset, title, ...stepProps } = props;
  const stepOffset = offset || 0;

  const steps = Children.map(children, (child, index) => {
    if (child.type !== Step) {
      throw new Error("StepList expects all children to be <Step /> elements");
    }

    return cloneElement(child, {
      ...stepProps,
      number: index + 1 + stepOffset,
    });
  });

  return (
    <div className="margin-bottom-8">
      <Heading level="2" size="1">
        {title}
      </Heading>
      {description && <p>{description}</p>}
      {steps}
    </div>
  );
};

StepList.propTypes = {
  /**
   * Title of the Step List.
   */
  title: PropTypes.node.isRequired,
  /**
   * Description for the overall Step List.
   */
  description: PropTypes.node,
  /**
   * A single Step element or an array of Step elements
   */
  children: PropTypes.node.isRequired,
  /**
   *  Localized text for each step's start button.
   */
  startText: PropTypes.string.isRequired,
  /**
   *  Localized text for each step's resume button.
   */
  resumeText: PropTypes.string.isRequired,
  /**
   *  Localized text for each step's edit link.
   */
  editText: PropTypes.string.isRequired,
  /**
   * Localized text for each step's completed button.
   */
  completedText: PropTypes.string.isRequired,
  /**
   * Prefix for each step's number announced to screen reader
   * e.g instead of announcing "1", provide a value to announce "Step 1"
   */
  screenReaderNumberPrefix: PropTypes.string.isRequired,
  /**
   * Offset for the step numbers. For example, if this is `3`, the first
   * step in this list will be Step 4.
   */
  offset: PropTypes.number,
};

export default StepList;
