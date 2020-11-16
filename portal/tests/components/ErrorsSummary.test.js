import { mount, shallow } from "enzyme";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import ErrorsSummary from "../../src/components/ErrorsSummary";
import React from "react";
import { act } from "react-dom/test-utils";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      errors: new AppErrorInfoCollection([
        new AppErrorInfo({ message: "Mock error message" }),
      ]),
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
  describe("when errors is null", () => {
    it("does not render an alert", () => {
      const { wrapper } = render({ errors: null });

      expect(wrapper.isEmptyRender()).toBeTruthy();
    });
  });

  describe("when no errors exist", () => {
    it("does not render an alert", () => {
      const { wrapper } = render({ errors: new AppErrorInfoCollection() });

      expect(wrapper.isEmptyRender()).toBeTruthy();
    });
  });

  describe("when only one error exists", () => {
    it("renders the singular heading and error message", () => {
      const errors = new AppErrorInfoCollection([
        new AppErrorInfo({ message: "Mock error message" }),
      ]);
      const { wrapper } = render({ errors });

      expect(wrapper).toMatchInlineSnapshot(`
        <Alert
          className="margin-bottom-3"
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
      const errors = new AppErrorInfoCollection([
        new AppErrorInfo({ message: "Mock error message #1" }),
        new AppErrorInfo({ message: "Mock error message #2" }),
      ]);
      const { wrapper } = render({ errors });

      expect(wrapper.prop("heading")).toMatchInlineSnapshot(
        `"2 errors were encountered"`
      );
      expect(wrapper.find(".usa-list li")).toHaveLength(2);
    });

    it("renders the singular heading if all errors are duplicates", () => {
      const errors = new AppErrorInfoCollection([
        new AppErrorInfo({ message: "Mock error message #1" }),
        new AppErrorInfo({ message: "Mock error message #1" }),
        new AppErrorInfo({ message: "Mock error message #1" }),
      ]);

      const { wrapper } = render({ errors });

      expect(wrapper.prop("heading")).toMatchInlineSnapshot(
        `"An error was encountered"`
      );
    });

    it("removes any duplicate error messages", () => {
      const errors = new AppErrorInfoCollection([
        new AppErrorInfo({ message: "Mock error message #1" }),
        new AppErrorInfo({ message: "Mock error message #1" }),
        new AppErrorInfo({ message: "Mock error message #2" }),
      ]);
      const { wrapper } = render({ errors });

      expect(wrapper.find(".usa-list li")).toHaveLength(2);
      expect(wrapper.find(".usa-list li").first().text()).toBe(
        errors.items[0].message
      );
      expect(wrapper.find(".usa-list li").last().text()).toBe(
        errors.items[2].message
      );
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
          errors={
            new AppErrorInfoCollection([
              new AppErrorInfo({ message: "Mock error message" }),
            ])
          }
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

    it("does not scroll if there are no errors", () => {
      // Mount the component so useEffect is called
      const errors = new AppErrorInfoCollection();
      const mountComponent = true;
      render({ errors }, mountComponent);

      expect(global.scrollTo).not.toHaveBeenCalled();
    });
  });

  describe("when the errors change", () => {
    it("scrolls to the top of the window", () => {
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      act(() => {
        wrapper.setProps({
          errors: new AppErrorInfoCollection([
            new AppErrorInfo({ message: "New error" }),
          ]),
        });
      });

      expect(global.scrollTo).toHaveBeenCalledTimes(2);
      expect(global.scrollTo).toHaveBeenCalledWith(0, 0);
    });
  });
});
