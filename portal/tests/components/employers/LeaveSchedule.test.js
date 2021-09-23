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

  it("renders reduced schedule without documents", () => {
    render(<LeaveSchedule claim={REDUCED_CLAIM} />);
    expect(
      screen.getByRole("row", {
        name: "Reduced leave schedule Contact us at (833) 344‑7365 for details about the leave schedule.",
      })
    ).toBeInTheDocument();
  });

  it("renders reduced schedule with documents", () => {
    render(<LeaveSchedule claim={REDUCED_CLAIM} hasDocuments={true} />);
    expect(
      screen.getByText(/Download the attached documentation for more details./)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("cell", {
        name: "Download the attached documentation or contact us at (833) 344‑7365 for details about the leave schedule.",
      })
    ).toBeInTheDocument();
  });

  it("renders intermittent schedule without documents", () => {
    render(<LeaveSchedule claim={INTERMITTENT_CLAIM} />);
    expect(
      screen.getByRole("row", {
        name: "Intermittent leave Contact us at (833) 344‑7365 for details about the leave schedule.",
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

    expect(
      screen.getByRole("cell", {
        name: "Download the attached documentation or contact us at (833) 344‑7365 for details about the leave schedule.",
      })
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
        name: "Reduced leave schedule Contact us at (833) 344‑7365 for details about the leave schedule.",
      })
    ).toBeInTheDocument();
  });
});
