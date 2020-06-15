import React, { Children, cloneElement } from "react";
import Button from "./Button";
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
      <Button
        className="margin-top-4"
        onClick={props.onSubmit}
        disabled={props.submitDisabled}
        name="submit-list"
      >
        {props.submitButtonText}
      </Button>
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
   * If true, button is disabled and onSubmit callback is not
   * called when the button is clicked.
   */
  submitDisabled: PropTypes.bool,
  /**
   * Handler for submit button click.
   */
  onSubmit: PropTypes.func.isRequired,
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
