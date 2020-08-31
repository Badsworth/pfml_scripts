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
      completedText: "Completed",
      editText: "Edit",
      screenReaderNumberPrefix: "Step",
    };
  });

  it("renders component", () => {
    const wrapper = shallow(
      <StepList {...props}>
        <Step title="Step 1" stepHref="#" status="not_started">
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
        <Step title="Step 1" stepHref="#" status="not_started">
          Step Description
        </Step>
      </StepList>
    );

    expect(wrapper.find("p").text()).toBe(description);
  });

  it("throws error if children are not Step components", () => {
    const render = () => {
      shallow(
        <StepList {...props}>
          <div />
          <div />
        </StepList>
      );
    };

    expect(render).toThrowError();
  });

  it("passes Step props to children", () => {
    const wrapper = shallow(
      <StepList {...props}>
        <Step title="Step 1" stepHref="#" status="not_started">
          Step Description
        </Step>
        <Step title="Step 2" stepHref="#" status="disabled">
          Step Description
        </Step>
      </StepList>
    );

    const steps = wrapper.find("Step");

    expect(steps).toHaveLength(2);

    expect(steps.first().prop("resumeText")).toEqual(props.resumeText);
    expect(steps.get(1).props.editText).toEqual(props.editText);
  });

  it("increases the Step number by the offset prop", () => {
    const wrapper = shallow(
      <StepList {...props} offset={3}>
        <Step title="Upload documents" stepHref="#" status="not_started">
          Step Description
        </Step>
      </StepList>
    );

    const steps = wrapper.find("Step");
    expect(steps.first().prop("number")).toBe(4);
  });
});
