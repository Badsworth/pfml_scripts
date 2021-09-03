import Details from "../../src/components/Details";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Expandable Content",
    },
    customProps
  );

  const component = <Details {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("Details", () => {
  it("renders children", () => {
    const text = "Child Text";
    const child = <span>{text}</span>;
    const { wrapper } = render({ children: child, label: "Label" });
    const span = wrapper.find("span");

    expect(span.text()).toMatch(text);
  });

  it("uses label as summary", () => {
    const text = "This is your label";
    const { wrapper } = render({ label: text });
    const summary = wrapper.find("summary");

    expect(summary.text()).toMatch(text);
  });
});
