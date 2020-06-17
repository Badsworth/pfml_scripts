import React, { Children, cloneElement } from "react";
import ButtonLink from "./ButtonLink";
import PropTypes from "prop-types";
import Step from "./Step";
import Title from "./Title";

const StepList = (props) => {
  const {
    startText,
    resumeText,
    editText,
    completedText,
    screenReaderNumberPrefix,
  } = props;

  const children = Children.map(props.children, (child, index) => {
    if (child.type !== Step) {
      throw new Error("StepList expects all children to be <Step /> elements");
    }

    return cloneElement(child, {
      startText,
      resumeText,
      editText,
      completedText,
      screenReaderNumberPrefix,
      number: index + 1,
    });
  });

  return (
    <div>
      <Title>{props.title}</Title>
      {children}
      <ButtonLink
        className="margin-top-4"
        href={props.submitPage}
        disabled={props.submitPageDisabled}
        name="submit-list"
      >
        {props.submitButtonText}
      </ButtonLink>
    </div>
  );
};

StepList.propTypes = {
  /**
   * Title of the Step List.
   */
  title: PropTypes.string.isRequired,
  /**
   * Localized text for submit button.
   */
  submitButtonText: PropTypes.string.isRequired,
  /**
   * Disable ability for user to click through to submit page
   */
  submitPageDisabled: PropTypes.bool,
  /**
   * Route to page where user can review / submit data.
   */
  submitPage: PropTypes.string.isRequired,
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
};

export default StepList;
