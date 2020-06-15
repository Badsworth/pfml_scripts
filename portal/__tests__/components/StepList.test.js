import { mount, shallow } from "enzyme";
import React from "react";
import Step from "../../src/components/Step";
import StepList from "../../src/components/StepList";

describe("StepList", () => {
  let props;

  beforeEach(() => {
    props = {
      title: "Step List",
      submitButtonText: "Submit",
      onSubmit: jest.fn(),
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

  it("handles submit", () => {
    const wrapper = shallow(
      <StepList {...props}>
        <Step title="Step 1" stepHref="#" status="not_started">
          Step Description
        </Step>
      </StepList>
    );

    wrapper.find({ name: "submit-list" }).simulate("click");

    expect(props.onSubmit).toHaveBeenCalled();
  });

  describe("when submitDisabled is true", () => {
    it("does not call onSubmit", () => {
      // must mount so disabled attribute
      // can be passed to actual button element
      const wrapper = mount(
        <StepList {...props} submitDisabled>
          <Step title="Step 1" stepHref="#" status="not_started">
            Step Description
          </Step>
        </StepList>
      );

      wrapper.find("button[name='submit-list']").simulate("click");

      expect(props.onSubmit).toHaveBeenCalledTimes(0);
    });
  });
});
