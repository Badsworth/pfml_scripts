import { render, screen } from "@testing-library/react";
import LeaveDatesAlert from "../../src/components/LeaveDatesAlert";
import React from "react";

jest.mock("../../src/hooks/useUniqueId");

const testApplicationSplit = {
  crossed_benefit_year: {
    benefit_year_end_date: "2021-02-01",
    benefit_year_start_date: "2020-02-03",
    current_benefit_year: true,
    employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
  },
  application_dates_in_benefit_year: {
    start_date: "2021-01-01",
    end_date: "2021-02-01",
  },
  application_dates_outside_benefit_year: {
    start_date: "2021-02-02",
    end_date: "2021-03-31",
  },
  application_outside_benefit_year_submittable_on: "2020-12-02",
};

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

  it("renders two leave dates and waiting periods when applicationSplit is passed in and the feature flag is on", () => {
    process.env.featureFlags = JSON.stringify({
      splitClaimsAcrossBY: true,
    });

    render(
      <LeaveDatesAlert
        startDate="2021-01-01"
        endDate="2021-03-31"
        showWaitingDayPeriod
        applicationSplit={testApplicationSplit}
      />
    );

    expect(screen.getAllByRole("heading")).toHaveLength(2);
    // two leave dates + two waiting periods = four total list items
    expect(screen.getAllByRole("listitem")).toHaveLength(4);
    expect(screen.getByText("1/1/2021 to 2/1/2021")).toBeInTheDocument();
    expect(screen.getByText("2/2/2021 to 3/31/2021")).toBeInTheDocument();
    expect(screen.getByText("1/1/2021 to 1/7/2021")).toBeInTheDocument();
    expect(screen.getByText("2/2/2021 to 2/8/2021")).toBeInTheDocument();
  });
});
