import React, { Children, cloneElement } from "react";
import Heading from "./core/Heading";
import Step from "./Step";
import isBlank from "../utils/isBlank";

interface StepListProps {
  /**
   * Title of the Step List.
   */
  title: React.ReactNode;
  /**
   * Description for the overall Step List.
   */
  description?: React.ReactNode;
  /**
   * A single Step element or an array of Step elements
   */
  children: JSX.Element | JSX.Element[];
  /**
   * Localized text for each step's start button.
   */
  startText: string;
  /**
   * Localized text for each step's resume button.
   */
  resumeText: string;
  /**
   * Localized text for each step's resume button aria-label,
   * needed for screen readers, since VoiceOver reads "résumé".
   */
  resumeScreenReaderText: string;
  /**
   * Localized text for each step's edit link.
   */
  editText: string;
  /**
   * Prefix for each step's number announced to screen reader
   * e.g instead of announcing "1", provide a value to announce "Step 1"
   */
  screenReaderNumberPrefix: string;
}

const StepList = (props: StepListProps) => {
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
      <Heading level="2" size="2">
        {title}
      </Heading>
      {!isBlank(description) && <p>{description}</p>}
      {steps}
    </div>
  );
};

export default StepList;
