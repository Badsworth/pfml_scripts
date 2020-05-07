import { mount, shallow } from "enzyme";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import ErrorsSummary from "../../src/components/ErrorsSummary";
import React from "react";
import { act } from "react-dom/test-utils";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      errors: [new AppErrorInfo({ message: "Mock error message" })],
    },
    customProps
  );

  const component = <ErrorsSummary {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component),
  };
}

describe("ErrorsSummary", () => {
  describe("when no errors exist", () => {
    it("does not render an alert", () => {
      const { wrapper } = render({ errors: null });

      expect(wrapper.isEmptyRender()).toBeTruthy();
    });
  });

  describe("when only one error exists", () => {
    it("renders the singular heading and error message", () => {
      const errors = [new AppErrorInfo({ message: "Mock error message" })];
      const { wrapper } = render({ errors });

      expect(wrapper).toMatchInlineSnapshot(`
        <Alert
          heading="An error was encountered"
          role="alert"
        >
          <p>
            Mock error message
          </p>
        </Alert>
      `);
    });
  });

  describe("when more than one error exists", () => {
    it("renders the plural heading and list of error messages", () => {
      const errors = [
        new AppErrorInfo({ message: "Mock error message #1" }),
        new AppErrorInfo({ message: "Mock error message #2" }),
      ];
      const { wrapper } = render({ errors });

      // Not taking a full snapshot since the IDs of the list items
      // change on each test run (which is expected)
      expect(wrapper.prop("heading")).toMatchInlineSnapshot(
        `"2 errors were encountered"`
      );
      expect(wrapper.find(".usa-list li")).toHaveLength(2);
    });
  });

  describe("when the component mounts", () => {
    it("focuses the Alert", () => {
      // Hide warning about rendering in the body, since we need to for this test
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

      // Mount the component so useEffect is called
      // attachTo the body so document.activeElement works (https://github.com/enzymejs/enzyme/issues/2337#issuecomment-608984530)
      const wrapper = mount(
        <ErrorsSummary
          errors={[new AppErrorInfo({ message: "Mock error message" })]}
        />,
        { attachTo: document.body }
      );

      const alert = wrapper.find("Alert").getDOMNode();
      expect(document.activeElement).toBe(alert);
    });

    it("scrolls to the top of the window", () => {
      // Mount the component so useEffect is called
      const mountComponent = true;
      render({}, mountComponent);

      expect(global.scrollTo).toHaveBeenCalledWith(0, 0);
    });
  });

  describe("when the errors change", () => {
    it("scrolls to the top of the window", () => {
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      act(() => {
        wrapper.setProps({
          errors: [new AppErrorInfo({ message: "New error" })],
        });
      });

      expect(global.scrollTo).toHaveBeenCalledTimes(2);
      expect(global.scrollTo).toHaveBeenCalledWith(0, 0);
    });
  });
});
