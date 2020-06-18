import React from "react";
import Step from "src/components/Step";

export default {
  title: "Components/StepList/Step",
  component: Step,
};

export const NotStarted = () => (
  <Step
    number={1}
    screenReaderNumberPrefix="Step"
    status="not_started"
    title="The First Step"
    startText="Start"
    resumeText="Resume"
    completedText="Completed"
    editText="Edit"
    stepHref="/"
  >
    These are the instructions
  </Step>
);

export const InProgress = () => (
  <Step
    number={1}
    screenReaderNumberPrefix="Step"
    status="in_progress"
    title="The First Step"
    startText="Start"
    resumeText="Resume"
    completedText="Completed"
    editText="Edit"
    stepHref="/"
  >
    These are the instructions
  </Step>
);

export const Disabled = () => (
  <Step
    number={1}
    screenReaderNumberPrefix="Step"
    status="disabled"
    title="The First Step"
    startText="Start"
    resumeText="Resume"
    completedText="Completed"
    editText="Edit"
    stepHref="/"
  >
    These are the instructions
  </Step>
);

export const Completed = () => (
  <Step
    number={1}
    screenReaderNumberPrefix="Step"
    status="completed"
    title="The First Step"
    startText="Start"
    resumeText="Resume"
    completedText="Completed"
    editText="Edit"
    stepHref="/"
  >
    These are the instructions
  </Step>
);
