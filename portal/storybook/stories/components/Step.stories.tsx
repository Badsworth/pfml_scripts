import { Props } from "storybook/types";
import React from "react";
import Step from "src/components/Step";

export default {
  title: "Components/StepList/Step",
  component: Step,
};

export const Default = (args: Props<typeof Step>) => {
  args.number ||= 1;
  return <Step {...args} />;
};

Default.args = {
  number: 1,
  screenReaderNumberPrefix: "Step",
  status: "not_started",
  title: "The First Step",
  startText: "Start",
  resumeText: "Resume",
  completedText: "Completed",
  editText: "Edit",
  stepHref: "/",
  children: "These are the instructions",
  editable: true,
};

export const NotStarted = () => (
  <Step
    editable
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
    editable
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
    editable
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

export const NotApplicable = () => (
  <Step
    editable
    number={1}
    screenReaderNumberPrefix="Step"
    status="not_applicable"
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
    editable
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

export const Submitted = () => (
  // @ts-expect-error ts-migrate(2741) FIXME: Property 'editable' is missing in type '{ children... Remove this comment to see the full error message
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
