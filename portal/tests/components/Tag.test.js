import { render, screen } from "@testing-library/react";
import React from "react";
import Tag from "../../src/components/Tag";

describe("Tag", () => {
  it.each(["error", "inactive", "pending", "success", "warning"])(
    "render tag with %s classes",
    (state) => {
      render(<Tag state={state} label="Foo" />);

      expect(screen.getByText("Foo")).toBeInTheDocument();
      expect(screen.getByText("Foo").classList.toString()).toMatchSnapshot();
    }
  );

  it("does not have default padding when alternative className padding-x is given", () => {
    const { container } = render(
      <Tag state="pending" label="Foo" className="padding-x-1" />
    );

    expect(container.firstChild).not.toHaveClass("padding-x-205");
    expect(container.firstChild).toHaveClass("padding-x-1");
  });
});
