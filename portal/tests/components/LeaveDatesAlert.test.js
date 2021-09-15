import { render, screen } from "@testing-library/react";
import LeaveDatesAlert from "../../src/components/LeaveDatesAlert";
import React from "react";

describe("LeaveDatesAlert", () => {
  it("renders Alert with given dates", () => {
    const { container } = render(
      <LeaveDatesAlert startDate="2021-01-01" endDate="2021-01-30" />
    );

    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders Alert with custom headingLevel", () => {
    render(
      <LeaveDatesAlert
        startDate="2021-01-01"
        endDate="2021-01-30"
        headingLevel="3"
      />
    );
    expect(screen.getByRole("heading")).toMatchInlineSnapshot(`
      <h3
        class="usa-alert__heading font-heading-md text-bold"
      >
        Your leave dates for paid leave
      </h3>
    `);
  });

  it("is empty render when one of the dates is missing", () => {
    const { container } = render(<LeaveDatesAlert startDate="2021-01-01" />);

    expect(container.firstChild).toBeNull();
  });
});
