import ConditionalContent from "../../src/components/ConditionalContent";
import React from "react";
import { shallow } from "enzyme";

describe("<ConditionalContent>", () => {
  describe("given `visible` prop is set to true", () => {
    it("renders the children", () => {
      const wrapper = shallow(
        <ConditionalContent removeField={jest.fn()} visible>
          <h1>Hello</h1>
        </ConditionalContent>
      );

      expect(wrapper.exists("h1")).toBe(true);
    });

    it("does not clear the fields when component unmounts", () => {
      const removeField = jest.fn();
      const wrapper = shallow(
        <ConditionalContent
          removeField={removeField}
          fieldNamesClearedWhenHidden={["foo", "bar"]}
          visible
        >
          <h1>Hello</h1>
        </ConditionalContent>
      );

      wrapper.unmount();

      expect(removeField).toHaveBeenCalledTimes(0);
    });
  });

  describe("given `visible` prop is set to false", () => {
    it("does not render anything", () => {
      const wrapper = shallow(
        <ConditionalContent removeField={jest.fn()} visible={false}>
          <h1>Hello</h1>
        </ConditionalContent>
      );

      expect(wrapper.isEmptyRender()).toBe(true);
    });

    it("clears all fields when component unmounts", () => {
      const removeField = jest.fn();
      const wrapper = shallow(
        <ConditionalContent
          removeField={removeField}
          fieldNamesClearedWhenHidden={["foo", "bar"]}
          visible={false}
        >
          <h1>Hello</h1>
        </ConditionalContent>
      );

      wrapper.unmount();

      expect(removeField).toHaveBeenCalledTimes(2);
      expect(removeField).toHaveBeenNthCalledWith(1, "foo");
      expect(removeField).toHaveBeenNthCalledWith(2, "bar");
    });

    it("does not attempt clearing fields when component re-renders", () => {
      const removeField = jest.fn();
      const wrapper = shallow(
        <ConditionalContent
          removeField={removeField}
          fieldNamesClearedWhenHidden={["foo", "bar"]}
          visible={false}
        >
          <h1>Hello</h1>
        </ConditionalContent>
      );

      wrapper.update();

      expect(removeField).toHaveBeenCalledTimes(0);
    });
  });

  describe("given fieldNamesClearedWhenHidden is not defined", () => {
    it("does not attempting clearing fields when component unmounts", () => {
      const removeField = jest.fn();
      const wrapper = shallow(
        <ConditionalContent removeField={removeField} visible={false}>
          <h1>Hello</h1>
        </ConditionalContent>
      );

      wrapper.unmount();

      expect(removeField).toHaveBeenCalledTimes(0);
    });
  });
});
