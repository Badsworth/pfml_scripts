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

  it("applies small padding when paddingSm is set", () => {
    const { container } = render(<Tag state="pending" label="Foo" paddingSm />);

    expect(container.firstChild).toHaveClass("padding-x-1");
  });
});
