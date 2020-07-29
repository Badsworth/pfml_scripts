import ErrorBoundary from "../../src/components/ErrorBoundary";
import React from "react";
import { mount } from "enzyme";

describe("ErrorBoundary", () => {
  describe("when no errors are thrown by a descendant component", () => {
    const GoodComponent = () => <div>Hello</div>;

    it("renders its descendant components", () => {
      const wrapper = mount(
        <ErrorBoundary>
          <GoodComponent />
        </ErrorBoundary>
      );

      expect(wrapper.find("GoodComponent")).toHaveLength(1);
      expect(wrapper.find("Alert")).toHaveLength(0);
    });
  });

  describe("when an error is thrown by a descendant component", () => {
    const originalLocation = window.location;
    const BadComponent = () => {
      throw new Error("Component broke.");
    };

    beforeEach(() => {
      delete window.location;
      window.location = { reload: jest.fn() };

      // Hide logged errors since that's expected in this scenario
      jest.spyOn(console, "error").mockImplementation(jest.fn());
    });

    afterEach(() => {
      window.location = originalLocation;
      jest.restoreAllMocks();
    });

    it("renders an Alert", () => {
      const wrapper = mount(
        <ErrorBoundary>
          <BadComponent />
        </ErrorBoundary>
      );

      expect(wrapper.find("BadComponent")).toHaveLength(0);
      expect(wrapper.find("Alert")).toMatchSnapshot();
    });

    it("reloads page when reload button is clicked", () => {
      const wrapper = mount(
        <ErrorBoundary>
          <BadComponent />
        </ErrorBoundary>
      );

      wrapper.find("Button").simulate("click");

      expect(window.location.reload).toHaveBeenCalledTimes(1);
    });
  });
});
