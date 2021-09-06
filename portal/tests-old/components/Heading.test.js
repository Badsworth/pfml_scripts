import Heading from "../../src/components/Heading";
import React from "react";
import { shallow } from "enzyme";

describe("Heading", () => {
  describe("when className is set", () => {
    it("adds the className to the other heading classes", () => {
      const wrapper = shallow(
        <Heading className="margin-bottom-2" level="2">
          Hello world
        </Heading>
      );

      expect(wrapper.hasClass("margin-bottom-2")).toBe(true);
      expect(wrapper.prop("className").length > "margin-bottom-2".length).toBe(
        true
      );
    });
  });

  describe("when weight prop is set", () => {
    it("overrides default heading weight", () => {
      const boldWrapper = shallow(
        <Heading level="2" weight="bold">
          Hello world
        </Heading>
      );
      const normalWrapper = shallow(
        <Heading level="2" weight="normal">
          Hello world
        </Heading>
      );

      expect(boldWrapper.hasClass("text-bold")).toBe(true);
      expect(boldWrapper.hasClass("text-normal")).toBe(false);

      expect(normalWrapper.hasClass("text-bold")).toBe(false);
      expect(normalWrapper.hasClass("text-normal")).toBe(true);
    });
  });

  describe("when only the level prop is set", () => {
    describe("given level is 2", () => {
      it("renders h2 with Level 2 class names", () => {
        const level = "2";

        const wrapper = shallow(<Heading level={level}>Hello world</Heading>);

        expect(wrapper).toMatchInlineSnapshot(`
          <h2
            className="font-heading-md text-bold"
          >
            Hello world
          </h2>
        `);
      });
    });

    describe("given level is 3", () => {
      it("renders h3 with Level 3 class names", () => {
        const level = "3";

        const wrapper = shallow(<Heading level={level}>Hello world</Heading>);

        expect(wrapper).toMatchInlineSnapshot(`
          <h3
            className="font-heading-sm text-bold"
          >
            Hello world
          </h3>
        `);
      });
    });

    describe("given level is 4", () => {
      it("renders h4 with Level 4 class names", () => {
        const level = "4";

        const wrapper = shallow(<Heading level={level}>Hello world</Heading>);

        expect(wrapper).toMatchInlineSnapshot(`
          <h4
            className="font-heading-xs text-bold"
          >
            Hello world
          </h4>
        `);
      });
    });

    describe("given level is 5", () => {
      it("renders h5 with Level 5 class names", () => {
        const level = "5";

        const wrapper = shallow(<Heading level={level}>Hello world</Heading>);

        expect(wrapper).toMatchInlineSnapshot(`
          <h5
            className="font-heading-2xs text-normal"
          >
            Hello world
          </h5>
        `);
      });
    });

    describe("given level is 6", () => {
      it("renders h6 with Level 6 class names", () => {
        const level = "6";

        const wrapper = shallow(<Heading level={level}>Hello world</Heading>);

        expect(wrapper).toMatchInlineSnapshot(`
          <h6
            className="font-heading-2xs text-normal"
          >
            Hello world
          </h6>
        `);
      });
    });
  });

  describe("when the size prop is set, in addition to level", () => {
    it("renders an HTML heading corresponding to the level prop", () => {
      // We'll generate the size by subtracting from the level
      const levels = [2, 3, 4, 5, 6];

      levels.forEach((level) => {
        const wrapper = shallow(
          <Heading level={`${level}`} size={`${level - 1}`}>
            Hello world
          </Heading>
        );

        expect(wrapper.is(`h${level}`)).toBe(true);
      });
    });

    describe("given size is 1", () => {
      it("renders with Level 1 class names", () => {
        const size = "1";

        const wrapper = shallow(
          <Heading level="2" size={size}>
            Hello world
          </Heading>
        );

        expect(wrapper).toMatchInlineSnapshot(`
          <h2
            className="font-heading-lg text-bold"
          >
            Hello world
          </h2>
        `);
      });
    });

    describe("given size is 2", () => {
      it("renders with Level 2 class names", () => {
        const size = "2";

        const wrapper = shallow(
          <Heading level="2" size={size}>
            Hello world
          </Heading>
        );

        expect(wrapper).toMatchInlineSnapshot(`
          <h2
            className="font-heading-md text-bold"
          >
            Hello world
          </h2>
        `);
      });
    });

    describe("given size is 3", () => {
      it("renders with Level 3 class names", () => {
        const size = "3";

        const wrapper = shallow(
          <Heading level="2" size={size}>
            Hello world
          </Heading>
        );

        expect(wrapper).toMatchInlineSnapshot(`
          <h2
            className="font-heading-sm text-bold"
          >
            Hello world
          </h2>
        `);
      });
    });

    describe("given size is 4", () => {
      it("renders with Level 4 class names", () => {
        const size = "4";

        const wrapper = shallow(
          <Heading level="2" size={size}>
            Hello world
          </Heading>
        );

        expect(wrapper).toMatchInlineSnapshot(`
          <h2
            className="font-heading-xs text-bold"
          >
            Hello world
          </h2>
        `);
      });
    });

    describe("given size is 5", () => {
      it("renders with Level 5 class names", () => {
        const size = "5";

        const wrapper = shallow(
          <Heading level="2" size={size}>
            Hello world
          </Heading>
        );

        expect(wrapper).toMatchInlineSnapshot(`
          <h2
            className="font-heading-2xs text-normal"
          >
            Hello world
          </h2>
        `);
      });
    });

    describe("given size is 6", () => {
      it("renders with Level 6 class names", () => {
        const size = "6";

        const wrapper = shallow(
          <Heading level="2" size={size}>
            Hello world
          </Heading>
        );

        expect(wrapper).toMatchInlineSnapshot(`
          <h2
            className="font-heading-2xs text-normal"
          >
            Hello world
          </h2>
        `);
      });
    });
  });
});
