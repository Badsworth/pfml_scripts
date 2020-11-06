import React from "react";
import ReviewRow from "../../src/components/ReviewRow";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Medical",
      label: "Leave type",
      level: "3",
    },
    customProps
  );
  const component = <ReviewRow {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("ReviewRow", () => {
  it("accepts a string as children", () => {
    const { wrapper } = render({
      children: "Medical",
    });

    expect(wrapper.text()).toMatch("Medical");
  });

  it("accepts HTML as children", () => {
    const { wrapper } = render({
      children: <p className="test-html">Medical</p>,
    });

    expect(wrapper.find(".test-html")).toHaveLength(1);
  });

  it("excludes border classes when noBorder is set", () => {
    const { wrapper: borderlessRow } = render({
      noBorder: true,
    });
    const { wrapper: borderedRow } = render();

    expect(borderedRow.prop("className")).toMatch("border");
    expect(borderlessRow.prop("className")).not.toMatch("border");
  });

  describe("when editHref is defined", () => {
    it("renders with an edit link", () => {
      const { wrapper } = render({
        editHref: "/name",
        editText: "Edit name",
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when editHref is not defined", () => {
    it("does not render an edit link", () => {
      const { wrapper } = render();

      expect(wrapper.find("a")).toHaveLength(0);
    });
  });
});
