import Button from "./Button";
import ButtonLink from "./ButtonLink";
import Heading from "./Heading";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import StepNumber from "./StepNumber";
import classnames from "classnames";

const Step = (props) => {
  const disabled = props.status === "disabled";
  const notStarted = props.status === "not_started";
  const inProgress = props.status === "in_progress";
  const completed = props.status === "completed";
  const notApplicable = props.status === "not_applicable";
  const showChildren = inProgress || notStarted || notApplicable;

  const editCompletedStep = (
    <React.Fragment>
      <div>
        <span className="padding-right-05 text-secondary">
          <svg width="20" height="11" viewBox="0 0 20 11">
            <path
              fill="currentColor"
              fillRule="evenodd"
              d="M15.783 1.242L14.73.212A.725.725 0 0 0 14.204 0a.725.725 0 0 0-.527.212L8.6 5.189 6.322 2.955a.724.724 0 0 0-.526-.213.725.725 0 0 0-.526.212l-1.053 1.03A.695.695 0 0 0 4 4.5c0 .202.072.374.217.515l2.802 2.743 1.053 1.03c.145.141.32.212.527.212.206 0 .382-.07.526-.212l1.053-1.03 5.605-5.485A.695.695 0 0 0 16 1.758a.694.694 0 0 0-.217-.515z"
            />
          </svg>
        </span>
        {props.completedText}
      </div>
      {props.stepHref && (
        <div className="margin-top-1">
          <Link href={props.stepHref}>
            <a
              className="usa-link"
              aria-label={`${props.editText}: ${props.title}`}
            >
              {props.editText}
            </a>
          </Link>
        </div>
      )}
    </React.Fragment>
  );

  const disabledStartButton = (
    <Button
      className="width-auto"
      aria-label={`${props.startText}: ${props.title}`}
      disabled
    >
      {props.startText}
    </Button>
  );

  const startButton = (
    <ButtonLink
      href={props.stepHref}
      className="width-auto"
      ariaLabel={`${props.startText}: ${props.title}`}
    >
      {props.startText}
    </ButtonLink>
  );

  const resumeButton = (
    <ButtonLink
      href={props.stepHref}
      className="width-auto"
      ariaLabel={`${props.resumeScreenReaderText}: ${props.title}`}
    >
      {props.resumeText}
    </ButtonLink>
  );

  // classes for wrapping element
  const classes = classnames(
    // allow step number and collapsible column to be flex-box
    "display-flex",
    "border-bottom",
    "border-base-light",
    "padding-y-3"
  );

  // parent column that contains a column
  // for title/description and another for user action
  const collapsibleColumnClasses = classnames(
    // fill the remainder of the row left after the step number
    "flex-fill",
    // give a little space next to step number
    "margin-left-2",
    // make this column also a row
    "grid-row",
    // push column down to center of step number
    "margin-top-1"
  );

  // column with the title and description
  const titleDescriptionColumnClasses = "tablet:grid-col-8";

  // lighten title color if step is disabled or not applicable
  const titleClasses = classnames({ "text-base": disabled || notApplicable });

  // column with user action links/button (edit, start, or resume)
  const actionColumnClasses = classnames(
    // on mobile, this column appears below title/description
    // so we need to add a little space
    "margin-top-2",
    // no margn needed on screen sizes larger than a tablet
    "tablet:margin-top-0",
    // align buttons and text to the right
    "tablet:text-right",
    "tablet:grid-col-4"
  );

  return (
    <div className={classes}>
      <StepNumber
        screenReaderPrefix={props.screenReaderNumberPrefix}
        state={props.status}
      >
        {props.number}
      </StepNumber>
      <div className={collapsibleColumnClasses}>
        <div className={titleDescriptionColumnClasses}>
          <Heading level="3" className={titleClasses}>
            {props.title}
          </Heading>
          {showChildren && <div className="usa-prose">{props.children}</div>}
          {completed && !props.editable && props.submittedContent}
        </div>
        <div className={actionColumnClasses}>
          {disabled && disabledStartButton}
          {notStarted && startButton}
          {inProgress && resumeButton}
          {completed && props.editable && editCompletedStep}
        </div>
      </div>
    </div>
  );
};

Step.propTypes = {
  /**
   * Href to question page.
   */
  stepHref: PropTypes.string,
  /**
   * Status of step.
   */
  status: PropTypes.oneOf([
    "disabled",
    "not_applicable",
    "not_started",
    "in_progress",
    "completed",
  ]).isRequired,
  /**
   * Title for the step.
   */
  title: PropTypes.string.isRequired,
  /**
   * Description of the step
   */
  children: PropTypes.node,
  /**
   * Content to display if step is submitted (completed && !editable)
   * TODO (CP-2354) Remove this once there are no submitted claims with null Other Leave data
   */
  submittedContent: PropTypes.node,
  /**
   * Whether or not the step is editable by the user
   */
  editable: PropTypes.bool.isRequired,
  /**
   * Localized text for the start button.
   * This can also be passed by parent StepList component.
   */
  startText: PropTypes.string,
  /**
   * Localized text for the resume button.
   * This can also be passed by parent StepList component.
   */
  resumeText: PropTypes.string,
  /**
   * Localized text for the resume button's aria-label,
   * needed for screen readers, since VoiceOver reads "résumé".
   * This can also be passed by parent StepList component.
   */
  resumeScreenReaderText: PropTypes.string,
  /**
   * Localized text for the edit link.
   * This can also be passed by parent StepList component.
   */
  editText: PropTypes.string,
  /**
   * Localized text for the completed button.
   */
  completedText: PropTypes.string.isRequired,
  /**
   * The number of the step in the step list.
   * This can also be passed by parent StepList component.
   */
  number: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  /**
   * Prefix for the number announced to screen reader
   * e.g instead of announcing "1", provide a value to announce "Step 1"
   * This can also be passed by parent StepList component.
   */
  screenReaderNumberPrefix: PropTypes.string,
};

export default Step;
