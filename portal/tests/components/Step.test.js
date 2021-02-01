import React from "react";
import Step from "../../src/components/Step";
import { shallow } from "enzyme";

describe("Step", () => {
  let props;
  const Child = () => <div>Description of step</div>;

  beforeEach(() => {
    props = {
      stepHref: "/path-to-step-question",
      startText: "Start",
      resumeText: "Resume",
      completedText: "Completed",
      editText: "Edit",
      editable: true,
      screenReaderNumberPrefix: "Step",
      number: "1",
      title: "Step Title",
    };
  });

  it("renders component", () => {
    const wrapper = shallow(
      <Step {...props} status="not_started">
        <Child />
      </Step>
    );

    expect(wrapper).toMatchSnapshot();
  });

  describe("when status is not_started", () => {
    it("shows children, displays start button", () => {
      const wrapper = shallow(
        <Step {...props} status="not_started">
          <Child />
        </Step>
      );

      expect(wrapper.find("Child")).toHaveLength(1);

      const buttonLink = wrapper.find("ButtonLink");
      expect(buttonLink.prop("children")).toEqual(props.startText);
    });
  });

  describe("when status is not_applicable", () => {
    it("shows children, does not show action links/buttons", () => {
      const wrapper = shallow(
        <Step {...props} status="not_applicable">
          <Child />
        </Step>
      );

      expect(wrapper.find("Child")).toHaveLength(1);

      expect(wrapper.find(".usa-link")).toHaveLength(0);
      expect(wrapper.contains("ButtonLink")).toBe(false);
    });
  });

  describe("when status is in_progress", () => {
    it("shows children, displays resume button", () => {
      const wrapper = shallow(
        <Step {...props} status="in_progress">
          <Child />
        </Step>
      );

      expect(wrapper.find("Child")).toHaveLength(1);

      const buttonLink = wrapper.find("ButtonLink");
      expect(buttonLink.prop("children")).toEqual(props.resumeText);
    });
  });

  describe("when status is completed", () => {
    it("does not show children, shows completed and edit link", () => {
      const wrapper = shallow(
        <Step {...props} status="completed">
          <Child />
        </Step>
      );

      expect(wrapper.find("Child")).toHaveLength(0);

      expect(wrapper.find(".usa-link")).toHaveLength(1);
    });

    it("hides edit link if editable is false", () => {
      const wrapper = shallow(
        <Step {...props} status="completed" editable={false}>
          <Child />
        </Step>
      );

      expect(wrapper.find(".usa-link")).toHaveLength(0);
    });
  });

  describe("when status is disabled", () => {
    it("does not show children, shows a disabled start button", () => {
      const wrapper = shallow(
        <Step {...props} status="disabled">
          <Child />
        </Step>
      );

      expect(wrapper.find("Child")).toHaveLength(0);

      expect(wrapper.find(".usa-link")).toHaveLength(0);
      expect(wrapper.contains("ButtonLink")).toBe(false);

      const button = wrapper.find("Button");
      expect(button.prop("children")).toEqual(props.startText);
      expect(button.prop("disabled")).toBe(true);
    });
  });
});
