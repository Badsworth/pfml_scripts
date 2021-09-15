import { render, screen } from "@testing-library/react";
import DocumentRequirements from "../../src/components/DocumentRequirements";
import React from "react";

describe("DocumentRequirements", () => {
  it("renders ID Document Requirements content", () => {
    render(<DocumentRequirements type="id" />);
    expect(screen.getByRole("heading")).toHaveAccessibleName(
      "Document Requirements:"
    );
    expect(screen.getByRole("list")).toMatchSnapshot();
  });

  it("renders Certification Document Requirements content", () => {
    render(<DocumentRequirements type="certification" />);
    expect(screen.getByRole("heading")).toHaveAccessibleName(
      "Document Requirements:"
    );
    expect(screen.getByRole("list")).toMatchSnapshot();
  });
});
