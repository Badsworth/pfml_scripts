import { mount, shallow } from "enzyme";
import ConditionalContent from "../../src/components/ConditionalContent";
import React from "react";
import { act } from "react-dom/test-utils";

describe("<ConditionalContent>", () => {
  function render(customProps = {}, mountComponent = false) {
    const props = Object.assign(
      {
        children: <h1>Hello</h1>,
        fieldNamesClearedWhenHidden: [],
        clearField: jest.fn(),
        getField: jest.fn(),
        updateFields: jest.fn(),
        visible: true,
      },
      customProps
    );

    const conditionalContent = <ConditionalContent {...props} />;

    return {
      props,
      wrapper: mountComponent
        ? mount(conditionalContent)
        : shallow(conditionalContent),
    };
  }

  describe("given `visible` prop is set to true", () => {
    it("renders the children", () => {
      const { wrapper } = render({ visible: true });
      expect(wrapper.exists("h1")).toBe(true);
    });

    it("restores previous data when prop `visible` changes from true -> false -> true", () => {
      const getField = (name) => name + "_fetched";
      const mountComponent = true;
      const { wrapper, props } = render(
        {
          children: <h2 name="world">World</h2>,
          fieldNamesClearedWhenHidden: ["world", "foo"],
          visible: true,
          getField,
        },
        mountComponent
      );

      act(() => {
        wrapper.setProps({ visible: false });
      });

      act(() => {
        wrapper.setProps({ visible: true });
      });

      expect(props.updateFields).toHaveBeenNthCalledWith(1, {
        world: "world_fetched",
        foo: "foo_fetched",
      });
    });
  });

  describe("given `visible` prop is set to false", () => {
    it("does not render anything", () => {
      const { wrapper } = render({ visible: false });

      expect(wrapper.isEmptyRender()).toBe(true);
    });

    it("clears all fields when component is hidden", () => {
      const mountComponent = true;
      const clearField = jest.fn();
      const { wrapper } = render(
        {
          visible: true,
          fieldNamesClearedWhenHidden: ["foo", "bar"],
          clearField,
        },
        mountComponent
      );

      act(() => {
        wrapper.setProps({ visible: false });
      });

      expect(clearField).toHaveBeenCalledTimes(2);
      expect(clearField).toHaveBeenNthCalledWith(1, "foo");
      expect(clearField).toHaveBeenNthCalledWith(2, "bar");
    });

    it("does not attempt clearing fields when component re-renders", () => {
      const clearField = jest.fn();
      const mountComponent = true;
      const { wrapper } = render(
        {
          visible: true,
          clearField,
          fieldNamesClearedWhenHidden: ["foo", "bar"],
        },
        mountComponent
      );

      wrapper.update();
      expect(clearField).toHaveBeenCalledTimes(0);
    });
  });

  describe("given fieldNamesClearedWhenHidden is not defined", () => {
    it("does not attempting clearing fields when component is hidden", () => {
      const clearField = jest.fn();
      const mountComponent = true;
      const { wrapper } = render(
        { clearField, visible: false },
        mountComponent
      );
      wrapper.setProps({ visible: false });

      expect(clearField).toHaveBeenCalledTimes(0);
    });
  });
});
