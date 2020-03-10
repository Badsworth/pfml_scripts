import React from "react";
import Title from "../../src/components/Title";
import { shallow } from "enzyme";

describe("Title", () => {
  describe("when the component prop isn't set", () => {
    it("renders an <h1>", () => {
      const wrapper = shallow(<Title>Hello world</Title>);

      expect(wrapper).toMatchInlineSnapshot(`
        <h1
          className="font-heading-xl line-height-sans-2 margin-top-0 margin-bottom-2"
        >
          Hello world
        </h1>
      `);
    });
  });

  describe("when the component prop is set to 'legend'", () => {
    it("renders a <legend>", () => {
      const wrapper = shallow(<Title component="legend">Hello world</Title>);

      expect(wrapper.hasClass("usa-legend")).toBe(true);
      expect(wrapper).toMatchInlineSnapshot(`
        <legend
          className="font-heading-xl line-height-sans-2 margin-top-0 margin-bottom-2 usa-legend"
        >
          Hello world
        </legend>
      `);
    });
  });
});
