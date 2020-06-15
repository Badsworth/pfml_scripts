import React from "react";
import StepNumber from "../../src/components/StepNumber";
import { shallow } from "enzyme";

describe("StepNumber", () => {
  it("renders the component", () => {
    const wrapper = shallow(
      <StepNumber screenReaderPrefix="Step" state="disabled">
        1
      </StepNumber>
    );

    expect(wrapper).toMatchInlineSnapshot(`
      <div
        className="radius-pill text-center height-3 width-3 tablet:height-5 tablet:width-5 font-sans-2xs tablet:font-sans-md border-2px line-height-sans-4 tablet:line-height-sans-5 border-base text-base"
      >
        <span
          className="usa-sr-only"
        >
          Step
        </span>
         
        1
      </div>
    `);
  });

  describe("when state is disabled", () => {
    it("renders an outlined number", () => {
      const wrapper = shallow(
        <StepNumber screenReaderPrefix="Step" state="disabled">
          1
        </StepNumber>
      );

      expect(wrapper.hasClass("border-2px")).toBe(true);
    });
  });

  describe("when state is completed", () => {
    it("renders an black filled number", () => {
      const wrapper = shallow(
        <StepNumber screenReaderPrefix="Step" state="completed">
          1
        </StepNumber>
      );

      expect(wrapper.hasClass("bg-black")).toBe(true);
    });
  });

  describe("when state is in_progress or not_started", () => {
    it("renders an secondary filled number", () => {
      const inProgress = shallow(
        <StepNumber screenReaderPrefix="Step" state="in_progress">
          1
        </StepNumber>
      );

      const notStarted = shallow(
        <StepNumber screenReaderPrefix="Step" state="not_started">
          1
        </StepNumber>
      );

      expect(inProgress.hasClass("bg-secondary")).toBe(true);
      expect(notStarted.hasClass("bg-secondary")).toBe(true);
    });
  });
});
