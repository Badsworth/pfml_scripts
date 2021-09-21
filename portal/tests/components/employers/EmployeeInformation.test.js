import { render, screen } from "@testing-library/react";
import EmployeeInformation from "../../../src/components/employers/EmployeeInformation";
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
});
