import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../../src/models/BenefitsApplication";
import { render, screen } from "@testing-library/react";
import IntermittentLeaveSchedule from "../../../src/components/employers/IntermittentLeaveSchedule";
import React from "react";

describe("IntermittentLeaveSchedule", () => {
  const regularIntermittentLeavePeriods = [
    new IntermittentLeavePeriod({
      leave_period_id: "mock-leave-period-id",
      start_date: "2021-02-01",
      end_date: "2021-07-01",
      duration: 3,
      duration_basis: DurationBasis.hours,
      frequency: 2,
      frequency_interval: null,
      frequency_interval_basis: FrequencyIntervalBasis.weeks,
    }),
  ];

  it("renders an irregular intermittent leave period", () => {
    const irregularIntermittentLeavePeriod = [
      new IntermittentLeavePeriod({
        leave_period_id: "mock-leave-period-id",
        start_date: "2021-02-01",
        end_date: "2021-07-01",
        duration: 3,
        duration_basis: DurationBasis.hours,
        frequency: 6,
        frequency_interval: 6,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      }),
    ];
    render(
      <table>
        <tbody>
          <IntermittentLeaveSchedule
            intermittentLeavePeriods={irregularIntermittentLeavePeriod}
          />
        </tbody>
      </table>
    );

    expect(screen.getByText(/Intermittent leave/)).toBeInTheDocument();
    expect(screen.getByText(/Contact us at/)).toBeInTheDocument();
  });

  it("renders a regular intermittent leave period", () => {
    render(
      <table>
        <tbody>
          <IntermittentLeaveSchedule
            intermittentLeavePeriods={regularIntermittentLeavePeriods}
          />
        </tbody>
      </table>
    );
    expect(screen.getByText(/Intermittent leave/)).toBeInTheDocument();
    expect(screen.getByText(/Contact us at/)).toBeInTheDocument();
  });

  it("renders correct text with documents", () => {
    render(
      <table>
        <tbody>
          <IntermittentLeaveSchedule
            hasDocuments
            intermittentLeavePeriods={regularIntermittentLeavePeriods}
          />
        </tbody>
      </table>
    );
    expect(screen.getByText(/Intermittent leave/)).toBeInTheDocument();
    expect(
      screen.getByText(/Download the attached documentation or contact us at/)
    ).toBeInTheDocument();
  });

  it("renders correct text without documents", () => {
    render(
      <table>
        <tbody>
          <IntermittentLeaveSchedule
            intermittentLeavePeriods={regularIntermittentLeavePeriods}
          />
        </tbody>
      </table>
    );

    expect(screen.getByText(/Intermittent leave/)).toBeInTheDocument();
    expect(screen.getByText(/Contact us at/)).toBeInTheDocument();
    expect(
      screen.queryByText(/Download the attached documentation or contact us at/)
    ).not.toBeInTheDocument();
  });
});
