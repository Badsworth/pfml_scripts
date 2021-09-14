import { render, screen } from "@testing-library/react";
import Details from "../../src/components/Details";
import React from "react";

describe("Details", () => {
  it("renders children", () => {
    render(
      <Details label="Expandable">
        <h1>Expandable Content</h1>
      </Details>
    );
    expect(
      screen.getByRole("heading", { name: /Expandable Content/ })
    ).toBeInTheDocument();
  });

  it("uses label as summary", () => {
    const { container } = render(
      <Details label="ExpandableLabel">
        <h1>Expandable Content</h1>
      </Details>
    );
    const summary = container.querySelector("summary");
    expect(summary).toHaveTextContent("Expandable");
  });
});
