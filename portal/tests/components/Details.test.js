import { render, screen } from "@testing-library/react";
import Details from "../../src/components/core/Details";
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
    render(
      <Details label="ExpandableLabel">
        <h1>Expandable Content</h1>
      </Details>
    );

    expect(screen.getByText("ExpandableLabel")).toBeInTheDocument();
  });
});
