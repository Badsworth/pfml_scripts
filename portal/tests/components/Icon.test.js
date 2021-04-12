import Icon from "../../src/components/Icon";
import React from "react";
import { shallow } from "enzyme";

function render(customProps = {}) {
  const props = Object.assign(
    {
      className: "",
    },
    customProps
  );
  const component = <Icon name="edit" {...props} />;
  return {
    component,
    wrapper: shallow(component),
  };
}

describe("Icon", () => {
  it("renders the component", () => {
    const { wrapper } = render();
    expect(wrapper).toMatchInlineSnapshot(`
      <svg
        aria-hidden="true"
        className="usa-icon"
        focusable="false"
        role="img"
      >
        <use
          xlinkHref="/img/sprite.svg#edit"
        />
      </svg>
    `);
  });

  describe("when className is set", () => {
    it("adds the className to the icon", () => {
      const { wrapper } = render({ className: "custom-class" });
      const svg = wrapper.find("svg");

      expect(svg.hasClass("custom-class")).toBe(true);
    });
  });

  describe("when fill is set", () => {
    it('adds "fill" to the svg', () => {
      const { wrapper } = render({ fill: "currentColor" });
      const svg = wrapper.find("svg");

      expect(svg.prop("fill")).toBe("currentColor");
    });
  });

  describe("when size is set", () => {
    it("adds the className to the icon", () => {
      const { wrapper } = render({ size: 4 });
      const svg = wrapper.find("svg");

      expect(svg.hasClass("usa-icon--size-4")).toBe(true);
      expect(svg.hasClass("usa-icon")).toBe(false);
    });
  });
});
