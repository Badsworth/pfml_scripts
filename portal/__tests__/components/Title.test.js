import React from "react";
import Title from "../../src/components/Title";
import { shallow } from "enzyme";

describe("Title", () => {
  describe("when the `component` prop isn't set", () => {
    it("renders an <h1>", () => {
      const wrapper = shallow(<Title>Hello world</Title>);

      expect(wrapper).toMatchInlineSnapshot(`
        <Fragment>
          <Head>
            <title>
              Hello world
            </title>
          </Head>
          <h1
            className="margin-top-0 margin-bottom-2 font-heading-lg line-height-sans-2"
          >
            Hello world
          </h1>
        </Fragment>
      `);
    });
  });

  describe("when the `component` prop is set to 'legend'", () => {
    it("renders a <legend>", () => {
      const wrapper = shallow(<Title component="legend">Hello world</Title>);

      expect(wrapper.find("legend").hasClass("usa-legend")).toBe(true);
      expect(wrapper).toMatchInlineSnapshot(`
        <Fragment>
          <Head>
            <title>
              Hello world
            </title>
          </Head>
          <legend
            className="margin-top-0 margin-bottom-2 font-heading-lg line-height-sans-2 usa-legend"
          >
            Hello world
          </legend>
        </Fragment>
      `);
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
        `"margin-top-0 margin-bottom-2 font-heading-sm line-height-sans-3"`
      );
    });
  });
});
