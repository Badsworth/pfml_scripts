import { render, screen } from "@testing-library/react";
import LeaveAdministratorRow from "../../../src/components/employers/LeaveAdministratorRow";
import React from "react";
import { UserLeaveAdministrator } from "../../../src/models/User";

const renderRow = (customProps) => {
  const props = {
    leaveAdmin: new UserLeaveAdministrator({
      employer_dba: "Dunder Mifflin",
      employer_fein: "11-111111",
      employer_id: "mock-employer-id",
      has_verification_data: true,
      verified: true,
    }),
    ...customProps,
  };
  return render(
    <table>
      <tbody>
        <LeaveAdministratorRow {...props} />
      </tbody>
    </table>
  );
};

describe("Leave Administrator Row", () => {
  it("renders expected initial data in the row", () => {
    renderRow();
    expect(screen.getByText(/Dunder Mifflin/)).toBeInTheDocument();
    expect(screen.getByText(/11-111111/)).toBeInTheDocument();
  });

  it("renders verification info as indicated", () => {
    const { container } = renderRow({
      leaveAdmin: new UserLeaveAdministrator({
        employer_dba: "Dunder Mifflin",
        employer_fein: "11-111111",
        employer_id: "mock-employer-id",
        has_verification_data: true,
        verified: false,
      }),
    });
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.getByText(/Verification required/)).toBeInTheDocument();
  });

  it("renders verification blocked info as indicated", () => {
    const { container } = renderRow({
      leaveAdmin: new UserLeaveAdministrator({
        employer_dba: "Dunder Mifflin",
        employer_fein: "11-111111",
        employer_id: "mock-employer-id",
        has_verification_data: false,
        verified: false,
      }),
    });
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.getByText(/Verification blocked/)).toBeInTheDocument();
  });
});
