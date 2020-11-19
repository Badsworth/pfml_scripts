import React from "react";
import Title from "../../src/components/Title";
import { shallow } from "enzyme";

describe("Title", () => {
  describe("when the `component` prop isn't set", () => {
    it("renders an <h1>", () => {
      const wrapper = shallow(<Title>Hello world</Title>);

      expect(wrapper).toMatchInlineSnapshot(`
        <Fragment>
          <HelmetWrapper
            defer={true}
            encodeSpecialCharacters={true}
          >
            <title>
              Hello world
            </title>
          </HelmetWrapper>
          <h1
            className="js-title margin-top-0 margin-bottom-2 font-heading-lg line-height-sans-2"
            tabIndex="-1"
          >
            Hello world
          </h1>
        </Fragment>
      `);
    });
  });

  it("adds a tabIndex and js-title class to the heading so we can manually move user focus to it", () => {
    const wrapper = shallow(<Title>Hello world</Title>);
    const h1 = wrapper.find("h1");

    expect(h1.hasClass("js-title")).toBe(true);
    expect(h1.prop("tabIndex")).toBe("-1");
  });

  describe("when the `bottomMargin` prop is set", () => {
    it("overrides the default bottom margin", () => {
      const defaultBottomMargin = shallow(<Title>Hello world</Title>).find(
        "h1"
      );
      const withBottomMargin = shallow(
        <Title marginBottom="4">Hello world</Title>
      ).find("h1");

      expect(defaultBottomMargin.hasClass("margin-bottom-2")).toBe(true);
      expect(withBottomMargin.hasClass("margin-bottom-2")).toBe(false);
      expect(withBottomMargin.hasClass("margin-bottom-4")).toBe(true);
    });
  });

  describe("when the `component` prop is set to 'legend'", () => {
    it("renders a <legend>", () => {
      const wrapper = shallow(<Title component="legend">Hello world</Title>);

      expect(wrapper.find("legend").hasClass("usa-legend")).toBe(true);
    });
  });

  describe("when the `hidden` prop is set to true", () => {
    it("visually hides the heading", () => {
      const heading = shallow(<Title hidden>Hello world</Title>).find("h1");

      expect(heading.hasClass("usa-sr-only")).toBe(true);
    });
  });

  describe("when the `seoTitle` prop is set", () => {
    it("overrides the text used for the <title>", () => {
      const wrapper = shallow(
        <Title seoTitle="Custom title">Default title</Title>
      );

      expect(wrapper.find("title").text()).toBe("Custom title");
      expect(wrapper.find("h1").text()).toBe("Default title");
    });
  });

  describe("when `small` is true", () => {
    it("adds classes for a smaller type size", () => {
      const wrapper = shallow(<Title small>Hello world</Title>);

      expect(wrapper.find("h1").prop("className")).toMatchInlineSnapshot(
        `"js-title margin-top-0 margin-bottom-2 font-heading-sm line-height-sans-3"`
      );
    });
  });
});
