import React from "react";
import ReviewHeading from "../../src/components/ReviewHeading";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      children: "Who is taking leave?",
      level: "2",
    },
    customProps
  );
  const component = <ReviewHeading {...props} />;

  return {
    props,
    wrapper: shallow(component),
  };
}

describe("ReviewHeading", () => {
  it("renders a Heading", () => {
    const { wrapper } = render();

    expect(wrapper).toMatchSnapshot();
  });

  describe("when editHref is defined", () => {
    it("renders with an edit link", () => {
      const { wrapper } = render({
        editHref: "/name",
        editText: "Edit",
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
