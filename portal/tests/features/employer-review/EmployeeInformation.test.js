import { render, screen } from "@testing-library/react";
import EmployeeInformation from "../../../src/features/employer-review/EmployeeInformation";
import { MockEmployerClaimBuilder } from "../../test-utils";
import React from "react";

const claim = new MockEmployerClaimBuilder().completed().create();

describe("EmployeeInformation", () => {
  it("renders the component", () => {
    const { container } = render(<EmployeeInformation claim={claim} />);
    expect(container).toMatchSnapshot();
  });

  it("renders one line break if second address line does not exist", () => {
    render(<EmployeeInformation claim={claim} />);
    expect(
      screen.getByTestId("residential-address").querySelectorAll("br").length
    ).toBe(1);
  });

  it("renders two line breaks if second address line exists", () => {
    const claimWithSecondAddressLine = new MockEmployerClaimBuilder()
      .address({
        city: "Boston",
        line_1: "1234 My St.",
        line_2: "Apt 1",
        state: "MA",
        zip: "00000",
      })
      .create();

    render(<EmployeeInformation claim={claimWithSecondAddressLine} />);

    expect(
      screen.getByTestId("residential-address").querySelectorAll("br").length
    ).toBe(2);
  });

  it("renders formatted date of birth", () => {
    render(<EmployeeInformation claim={claim} />);
    expect(screen.getByText("7/17/****")).toBeInTheDocument();
  });

  it("renders organization row", () => {
    render(<EmployeeInformation claim={claim} />);
    expect(
      screen.getByRole("heading", { name: "Organization" })
    ).toBeInTheDocument();
  });

  it("does not render organization row if there is no employer_dba", () => {
    const claimWithoutEmployerDba = { ...claim, employer_dba: null };
    render(<EmployeeInformation claim={claimWithoutEmployerDba} />);
    expect(
      screen.queryByRole("heading", { name: "Organization" })
    ).not.toBeInTheDocument();
  });

  it("renders the correct employee information hierarchy", () => {
    render(<EmployeeInformation claim={claim} />);
    const h3s = screen
      .getAllByRole("heading", { level: 3 })
      .map((h) => h.innerHTML);

    expect(h3s.includes("Organization")).toBe(true);
    expect(h3s.includes("Employer ID number (EIN)")).toBe(true);
  });
});
