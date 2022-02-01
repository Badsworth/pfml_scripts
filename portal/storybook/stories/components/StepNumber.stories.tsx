import React from "react";
import StepNumber from "src/components/StepNumber";

export default {
  title: "Features/Applications/StepList/StepNumber",
  component: StepNumber,
};

export const Default = () => (
  <StepNumber screenReaderPrefix="Number" state="completed">
    1
  </StepNumber>
);

export const NotStarted = () => (
  <StepNumber screenReaderPrefix="Number" state="not_started">
    1
  </StepNumber>
);

export const InProgress = () => (
  <StepNumber screenReaderPrefix="Number" state="in_progress">
    1
  </StepNumber>
);

export const Disabled = () => (
  <StepNumber screenReaderPrefix="Number" state="disabled">
    1
  </StepNumber>
);
