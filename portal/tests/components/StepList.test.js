import React from "react";
import Step from "../../src/components/Step";
import StepList from "../../src/components/StepList";
import { shallow } from "enzyme";

describe("StepList", () => {
  let props;

  beforeEach(() => {
    props = {
      title: "Step List",
      submitButtonText: "Submit",
      submitPage: "path/to/submit/page",
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

  describe("when submitDisabled is true", () => {
    it("disables button link", () => {
      // must mount so disabled attribute
      // can be passed to actual button element
      const wrapper = shallow(
        <StepList {...props} submitPageDisabled>
          <Step title="Step 1" stepHref="#" status="not_started">
            Step Description
          </Step>
        </StepList>
      );

      expect(wrapper.find("ButtonLink").prop("disabled")).toBe(true);
    });
  });
});
