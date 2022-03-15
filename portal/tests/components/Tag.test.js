import { render, screen } from "@testing-library/react";
import React from "react";
import Tag from "../../src/components/core/Tag";

describe("Tag", () => {
  it.each(["error", "inactive", "success", "warning"])(
    "render tag with %s classes",
    (state) => {
      render(<Tag state={state} label="Foo" />);

      expect(screen.getByText("Foo")).toBeInTheDocument();
      expect(screen.getByText("Foo").classList.toString()).toMatchSnapshot();
    }
  );

  it("supports className prop", () => {
    const { container } = render(<Tag label="Foo" className="margin-left-1" />);

    expect(container.firstChild).toHaveClass("margin-left-1");
  });
});
