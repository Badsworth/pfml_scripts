import { mount, shallow } from "enzyme";
import Alert from "../../src/components/Alert";
import React from "react";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Alert body text",
    },
    customProps
  );

  const component = <Alert {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("Alert", () => {
  it("renders the children as the alert body text", () => {
    const { wrapper } = render({ children: <p>Body text</p> });

    expect(wrapper.find(".usa-alert__text")).toMatchInlineSnapshot(`
      <div
        className="usa-alert__text"
      >
        <p>
          Body text
        </p>
      </div>
    `);
  });

  it("renders an h2 when the heading prop is set", () => {
    const { wrapper } = render({ heading: "Alert heading" });

    expect(wrapper.find("Heading")).toMatchInlineSnapshot(`
      <Heading
        className="usa-alert__heading"
        level="2"
      >
        Alert heading
      </Heading>
    `);
  });

  it("renders an h3 when headingLevel is set to 3", () => {
    const { wrapper } = render({ heading: "Alert heading", headingLevel: "3" });

    expect(wrapper.find("Heading").prop("level")).toBe("3");
    expect(wrapper.find("Heading").prop("size")).toBeUndefined();
  });

  it("renders overrides the Heading size when headingSize is set to 3", () => {
    const { wrapper } = render({ heading: "Alert heading", headingSize: "3" });

    expect(wrapper.find("Heading").prop("level")).toBe("2");
    expect(wrapper.find("Heading").prop("size")).toBe("3");
  });

  it("renders the 'error' state by default", () => {
    const { wrapper } = render();

    expect(wrapper.hasClass("usa-alert--error")).toBe(true);
  });

  it("forwards the ref to the alert element", () => {
    const alertRef = React.createRef();
    // We need to wrap this with another component in order to test this
    const wrapper = mount(
      <React.Fragment>
        <Alert ref={alertRef}>Test</Alert>
      </React.Fragment>
    );

    expect(wrapper.find(".usa-alert").instance()).toBe(alertRef.current);
  });

  describe("when the role prop isn't set", () => {
    it("adds role='region' to the alert body element", () => {
      const { wrapper } = render();

      const bodyElement = wrapper.find(".usa-alert__body");

      expect(bodyElement.prop("role")).toBe("region");
    });
  });

  describe("when the role prop is set", () => {
    it("adds the role to the alert body element", () => {
      const role = "alert";
      const { wrapper } = render({ role });

      const bodyElement = wrapper.find(".usa-alert__body");

      expect(bodyElement.prop("role")).toBe(role);
    });
  });

  it("renders the 'info' state when the state prop is set to 'info'", () => {
    const { wrapper } = render({ state: "info" });

    expect(wrapper.hasClass("usa-alert--info")).toBe(true);
  });

  it("renders the 'success' state when the state prop is set to 'success'", () => {
    const { wrapper } = render({ state: "success" });

    expect(wrapper.hasClass("usa-alert--success")).toBe(true);
  });

  it("renders the 'warning' state when the state prop is set to 'warning'", () => {
    const { wrapper } = render({ state: "warning" });

    expect(wrapper.hasClass("usa-alert--warning")).toBe(true);
  });

  it("renders with an icon when the noIcon prop is not set", () => {
    const { wrapper } = render();
    expect(wrapper.hasClass("usa-alert--no-icon")).toBe(false);
  });

  it("renders without an icon when the noIcon prop is set", () => {
    const { wrapper } = render({ noIcon: true });
    expect(wrapper.hasClass("usa-alert--no-icon")).toBe(true);
  });

  it("renders slim when the slim prop is set", () => {
    const { wrapper } = render({ slim: true });
    expect(wrapper.hasClass("usa-alert--slim")).toBe(true);
  });

  it("renders with a neutral background color when the neutral prop is set", () => {
    const { wrapper } = render({ neutral: true });
    expect(wrapper.hasClass("c-alert--neutral")).toBe(true);
  });

  it("renders auto-width when the autoWidth prop is set", () => {
    const { wrapper } = render({ autoWidth: true });
    expect(wrapper.hasClass("c-alert--auto-width")).toBe(true);
  });
});
