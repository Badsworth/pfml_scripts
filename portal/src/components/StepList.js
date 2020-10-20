import React, { Children, cloneElement } from "react";
import Heading from "./Heading";
import PropTypes from "prop-types";
import Step from "./Step";

const StepList = (props) => {
  const { children, description, title, ...stepProps } = props;

  const steps = Children.map(children, (child, index) => {
    if (child.type !== Step) {
      return child;
    }

    return cloneElement(child, {
      ...stepProps,
      number: child.props.number || index + 1,
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
   * Localized text for each step's start button.
   */
  startText: PropTypes.string.isRequired,
  /**
   * Localized text for each step's resume button.
   */
  resumeText: PropTypes.string.isRequired,
  /**
   * Localized text for each step's resume button aria-label,
   * needed for screen readers, since VoiceOver reads "résumé".
   */
  resumeScreenReaderText: PropTypes.string.isRequired,
  /**
   * Localized text for each step's edit link.
   */
  editText: PropTypes.string.isRequired,
  /**
   * Prefix for each step's number announced to screen reader
   * e.g instead of announcing "1", provide a value to announce "Step 1"
   */
  screenReaderNumberPrefix: PropTypes.string.isRequired,
};

export default StepList;
