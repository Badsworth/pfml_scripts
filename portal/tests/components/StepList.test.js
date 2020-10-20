import React from "react";
import Step from "../../src/components/Step";
import StepList from "../../src/components/StepList";
import { shallow } from "enzyme";

describe("StepList", () => {
  let props;

  beforeEach(() => {
    props = {
      title: "Step List",
      startText: "Start",
      resumeText: "Resume",
      resumeScreenReaderText: "Continue with",
      editText: "Edit",
      screenReaderNumberPrefix: "Step",
    };
  });

  it("renders component", () => {
    const wrapper = shallow(
      <StepList {...props}>
        <Step
          editable
          title="Step 1"
          stepHref="#"
          status="not_started"
          completedText="Completed"
        >
          Step Description
        </Step>
      </StepList>
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("renders a description", () => {
    const description = "Hello world";

    const wrapper = shallow(
      <StepList {...props} description={description}>
        <Step
          editable
          title="Step 1"
          stepHref="#"
          status="not_started"
          completedText="Completed"
        >
          Step Description
        </Step>
      </StepList>
    );

    expect(wrapper.find("p").text()).toBe(description);
  });

  it("passes Step props to children", () => {
    const wrapper = shallow(
      <StepList {...props}>
        <Step
          editable
          title="Step 1"
          stepHref="#"
          status="not_started"
          completedText="Completed"
        >
          Step Description
        </Step>
        <Step
          editable
          title="Step 2"
          stepHref="#"
          status="disabled"
          completedText="Completed"
        >
          Step Description
        </Step>
      </StepList>
    );

    const steps = wrapper.find("Step");

    expect(steps).toHaveLength(2);

    expect(steps.first().prop("resumeText")).toEqual(props.resumeText);
    expect(steps.get(1).props.editText).toEqual(props.editText);
  });

  it("does not override a Step number if one is defined", () => {
    const wrapper = shallow(
      <StepList {...props}>
        <Step
          editable
          number={4}
          title="Upload documents"
          stepHref="#"
          status="not_started"
          completedText="Completed"
        >
          Step Description
        </Step>
      </StepList>
    );

    const steps = wrapper.find("Step");
    expect(steps.first().prop("number")).toBe(4);
  });

  it("renders when children are not steps", () => {
    const TestComponent = () => <div />;
    const wrapper = shallow(
      <StepList {...props}>
        <TestComponent />
        <TestComponent />
      </StepList>
    );

    expect(wrapper.find(TestComponent)).toHaveLength(2);
  });
});
