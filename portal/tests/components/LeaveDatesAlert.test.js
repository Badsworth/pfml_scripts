import { render, screen } from "@testing-library/react";
import LeaveDatesAlert from "../../src/components/LeaveDatesAlert";
import React from "react";

jest.mock("../../src/hooks/useUniqueId");

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
        id="mock-unique-id"
      >
        Your leave dates for paid leave from PFML
      </h3>
    `);
  });

  it("with waiting period true, renders date range of wait period as expected", () => {
    render(
      <LeaveDatesAlert
        startDate="2021-01-01"
        endDate="2021-01-30"
        showWaitingDayPeriod={true}
      />
    );
    expect(
      screen.getByRole("heading", { name: "Your 7-day waiting period dates" })
    ).toBeInTheDocument();
    expect(screen.getByText("1/1/2021 to 1/7/2021")).toBeInTheDocument();
  });

  it("is empty render when one of the dates is missing", () => {
    const { container } = render(<LeaveDatesAlert startDate="2021-01-01" />);

    expect(container).toBeEmptyDOMElement();
  });

  it("renders 7 day waiting period when showWaitingDayPeriod is true", () => {
    render(
      <LeaveDatesAlert
        startDate="2021-01-31"
        endDate="2021-02-28"
        showWaitingDayPeriod
      />
    );

    expect(screen.getAllByRole("heading")).toHaveLength(2);
    expect(
      screen.getByText("Your 7-day waiting period dates").parentElement
    ).toMatchSnapshot();
  });
});
