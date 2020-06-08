import React from "react";
import ReviewRow from "../../src/components/ReviewRow";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Medical",
      heading: "Leave type",
    },
    customProps
  );
  const component = <ReviewRow {...props} />;

  return {
    props: customProps,
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
