import { render, screen } from "@testing-library/react";
import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";
import { MockEmployerClaimBuilder } from "../../test-utils";
import React from "react";

const CONTINUOUS_CLAIM = new MockEmployerClaimBuilder()
  .continuous()
  .absenceId()
  .create();
const REDUCED_CLAIM = new MockEmployerClaimBuilder()
  .reducedSchedule()
  .absenceId()
  .create();
const INTERMITTENT_CLAIM = new MockEmployerClaimBuilder()
  .intermittent()
  .absenceId()
  .create();

describe("LeaveSchedule", () => {
  it("renders continuous schedule without documents", () => {
    render(<LeaveSchedule claim={CONTINUOUS_CLAIM} />);
    expect(
      screen.getByRole("row", { name: "1/1/2021 to 6/1/2021 Continuous leave" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("This is your employee’s expected leave schedule.")
    ).toBeInTheDocument();
  });

  it("renders continuous schedule with documents", () => {
    render(<LeaveSchedule claim={CONTINUOUS_CLAIM} hasDocuments={true} />);
    expect(
      screen.getByText(/Download the attached documentation for more details./)
    ).toBeInTheDocument();
  });

  it("renders reduced schedule", () => {
    render(<LeaveSchedule claim={REDUCED_CLAIM} />);
    const row = screen.getByRole("row", {
      name: /Reduced leave schedule/i,
    });

    expect(row).toMatchSnapshot();
  });

  it("renders reference to downloading docs when reduced schedule claim has documents", () => {
    render(<LeaveSchedule claim={REDUCED_CLAIM} hasDocuments={true} />);
    expect(
      screen.getByText(/Download the attached documentation for more details./)
    ).toBeInTheDocument();
  });

  it("renders intermittent schedule without documents", () => {
    render(<LeaveSchedule claim={INTERMITTENT_CLAIM} />);
    expect(
      screen.getByRole("row", {
        name: "2/1/2021 to 7/1/2021 Intermittent leave",
      })
    ).toBeInTheDocument();
  });

  it("renders intermittent schedule with documents", () => {
    render(<LeaveSchedule claim={INTERMITTENT_CLAIM} hasDocuments={true} />);
    expect(
      screen.getByText(
        "Download the attached documentation for details about the employee’s intermittent leave schedule."
      )
    ).toBeInTheDocument();
  });

  it("renders multiple leave schedules", () => {
    const multipleLeaveClaim = new MockEmployerClaimBuilder()
      .completed()
      .create();
    render(<LeaveSchedule claim={multipleLeaveClaim} />);
    expect(
      screen.getByRole("row", { name: "1/1/2021 to 6/1/2021 Continuous leave" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("row", {
        name: "2/1/2021 to 7/1/2021 Reduced leave schedule",
      })
    ).toBeInTheDocument();
  });
});
