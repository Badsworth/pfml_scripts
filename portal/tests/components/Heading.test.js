import { render, screen } from "@testing-library/react";
import Heading from "../../src/components/Heading";
import React from "react";

describe("Heading", () => {
  describe("Heading classes", () => {
    it("adds the className to the other heading classes", () => {
      render(
        <Heading className="margin-bottom-2" level="2">
          Foobar
        </Heading>
      );

      const header = screen.getByRole("heading", { name: "Foobar" });
      expect(header).toHaveClass(
        "margin-bottom-2",
        "font-heading-md",
        "text-bold"
      );

      expect(header).toMatchSnapshot();
    });
  });

  describe("Heading weight", () => {
    it("default heading weight is correct", () => {
      render(
        <Heading level="2" weight="normal">
          Foobar
        </Heading>
      );
      const header = screen.getByRole("heading", { name: "Foobar" });
      expect(header).toHaveClass("text-normal");
      expect(header).not.toHaveClass("text-bold");
      expect(header).toMatchSnapshot();
    });

    it("overrides default heading weight", () => {
      render(
        <Heading level="2" weight="bold">
          Foobar
        </Heading>
      );

      const header = screen.getByRole("heading", { name: "Foobar" });
      expect(header).toHaveClass("text-bold");
      expect(header).not.toHaveClass("text-normal");
      expect(header).toMatchSnapshot();
    });
  });

  describe("Heading levels", () => {
    it("renders correct heading based on level", () => {
      const headingLevels = [2, 3, 4, 5, 6];

      headingLevels.forEach((headingLevel) => {
        render(<Heading level={`${headingLevel}`}>{headingLevel}</Heading>);
        const heading = screen.getByRole("heading", { name: headingLevel });
        expect(heading).toBeInTheDocument();
        expect(heading).toMatchSnapshot();
      });
    });
  });

  describe("Heading sizes", () => {
    it("renders the correct classes for available sizes", () => {
      // Classes for corresponding "sizes"
      const sizeClasses = {
        1: ["font-heading-lg", "text-bold"],
        2: ["font-heading-md", "text-bold"],
        3: ["font-heading-sm", "text-bold"],
        4: ["font-heading-xs", "text-bold"],
        5: ["font-heading-2xs", "text-normal"],
        6: ["font-heading-2xs", "text-normal"],
      };

      // Iterate through available sizes
      Object.keys(sizeClasses).forEach((size) => {
        // "size" string → number
        const sizeNumber = Number(size);

        // levels 2 through 6 (max)
        const level = sizeNumber === 6 ? 6 : sizeNumber + 1;

        render(
          <Heading level={`${level}`} size={size}>
            {size}
          </Heading>
        );

        const heading = screen.getByRole("heading", { name: size });

        expect(heading).toHaveClass(...sizeClasses[size]);
        expect(heading).toMatchSnapshot();
      });
    });
  });
});
