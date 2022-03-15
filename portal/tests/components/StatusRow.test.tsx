import React from "react";
import StatusRow from "../../src/components/StatusRow";
import { render } from "@testing-library/react";

describe("StatusRow", () => {
  it("renders the component", () => {
    const { container } = render(
      <StatusRow label="Test label">
        <p>Children</p>
      </StatusRow>
    );

    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders the component with additional class name", () => {
    const { container } = render(
      <StatusRow label="Test label" className="test-class">
        Test
      </StatusRow>
    );

    expect(container.firstChild).toHaveClass("test-class");
  });
});
