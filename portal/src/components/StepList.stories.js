import React from "react";
import Step from "./Step";
import StepList from "./StepList";

export default {
  title: "Components/StepList",
  component: StepList,
};

export const Default = () => (
  <StepList
    title="Title of StepList"
    startText="Start"
    resumeText="Resume"
    completedText="Completed"
    editText="Edit"
    submitButtonText="Submit the Steps"
    submitDisabled
    // eslint-disable-next-line no-alert
    onSubmit={() => alert("how wow, a step submission")}
  >
    <Step title="Step Title 1" status="completed" stepHref="#">
      This is the step instructions and should not be visible.
    </Step>
    <Step title="Step Title 2" status="in_progress" stepHref="#">
      This is the step instructions. Mauris fermentum justo eget augue
      sollicitudin consectetur eu eget urna. Etiam consectetur luctus tincidunt.
      Integer consectetur cursus pellentesque. In non rhoncus nunc.
      <ol className="usa-list">
        <li>Nulla pulvinar risus sed placerat dignissim</li>
        <li>Nulla pulvinar risus sed placerat dignissim</li>
        <li>Nulla pulvinar risus sed placerat dignissim</li>
      </ol>
    </Step>
    <Step title="Step Title 3" status="not_started" stepHref="#">
      This is the step instructions. Mauris fermentum justo eget augue
      sollicitudin consectetur eu eget urna. Etiam consectetur luctus tincidunt.
      Integer consectetur cursus pellentesque. In non rhoncus nunc.
      <ul className="usa-list">
        <li>Nulla pulvinar risus sed placerat dignissim</li>
        <li>Nulla pulvinar risus sed placerat dignissim</li>
        <li>Nulla pulvinar risus sed placerat dignissim</li>
      </ul>
    </Step>
    <Step title="Step Title 4" status="disabled" stepHref="#">
      This is the step instructions and should not be visible.
    </Step>
  </StepList>
);
