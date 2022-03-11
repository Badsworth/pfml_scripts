import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import { fireEvent, render, screen } from "@testing-library/react";
import AmendableEmployerBenefit from "../../../src/features/employer-review/AmendableEmployerBenefit";
import React from "react";
import userEvent from "@testing-library/user-event";

const onChange = jest.fn();
const onRemove = jest.fn();
const errors = [];
const employerBenefit = new EmployerBenefit({
  benefit_end_date: "2021-03-01",
  benefit_start_date: "2021-02-01",
  benefit_type: EmployerBenefitType.shortTermDisability,
  employer_benefit_id: 0,
  is_full_salary_continuous: true,
});

const renderComponent = (customProps) => {
  const props = {
    errors,
    employerBenefit,
    isAddedByLeaveAdmin: true,
    onChange,
    onRemove,
    shouldShowV2: false,
    ...customProps,
  };
  return render(
    <table>
      <tbody>
        <AmendableEmployerBenefit {...props} />
      </tbody>
    </table>
  );
};

const v2ExclusiveLabels = [
  /What kind of employer-sponsored benefit is it?/,
  /Does this employer-sponsored benefit fully replace your employee's wages?/,
];

describe("AmendableEmployerBenefit", () => {
  it("does not show v2 exclusive fields in v1", () => {
    renderComponent();
    v2ExclusiveLabels.forEach((label) => {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    });
  });

  it("shows v2 exclusive fields in v2", () => {
    renderComponent({ shouldShowV2: true });
    v2ExclusiveLabels.forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it("for amended benefits, it renders the existing data with amendment form hidden initially", () => {
    renderComponent({ isAddedByLeaveAdmin: false, shouldShowV2: true });
    expect(screen.getByText("2/1/2021 to 3/1/2021")).toBeInTheDocument();
    expect(
      screen.getByText(/Short-term disability insurance/)
    ).toBeInTheDocument();
    const amendButton = screen.getByRole("button", { name: "Amend" });
    expect(
      screen.queryByText(/Amend employer-sponsored benefit/)
    ).not.toBeInTheDocument();
    userEvent.click(amendButton);
    expect(
      screen.queryByText(/Amend employer-sponsored benefit/)
    ).toBeInTheDocument();
  });

  it("enables updates to start and end dates", () => {
    renderComponent({ isAddedByLeaveAdmin: false, shouldShowV2: true });
    const amendButton = screen.getByRole("button", { name: "Amend" });
    userEvent.click(amendButton);

    const [startMonthInput, endMonthInput] = screen.getAllByRole("textbox", {
      name: "Month",
    });
    const [startDayInput, endDayInput] = screen.getAllByRole("textbox", {
      name: "Day",
    });
    const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
      name: "Year",
    });
    expect(startYearInput).toHaveValue("2021");
    expect(startMonthInput).toHaveValue("02");
    expect(startDayInput).toHaveValue("01");
    expect(endMonthInput).toHaveValue("03");
    expect(endDayInput).toHaveValue("01");
    expect(endYearInput).toHaveValue("2021");
    expect(onChange).toHaveBeenCalledTimes(0);

    fireEvent.change(startMonthInput, { target: { value: "05" } });
    expect(onChange).toHaveBeenCalledWith(
      { benefit_start_date: "2021-05-01", employer_benefit_id: 0 },
      "amendedBenefits"
    );
    fireEvent.change(endMonthInput, { target: { value: "06" } });
    expect(onChange).toHaveBeenLastCalledWith(
      { benefit_end_date: "2021-06-01", employer_benefit_id: 0 },
      "amendedBenefits"
    );
    expect(startMonthInput).toHaveValue("05");
    expect(endMonthInput).toHaveValue("06");
  });

  it("formats empty dates as null instead of empty string", () => {
    renderComponent({ isAddedByLeaveAdmin: false, shouldShowV2: true });
    userEvent.click(screen.getByRole("button", { name: "Amend" }));
    const dayInputs = screen.getAllByRole("textbox", { name: "Day" });
    const monthInputs = screen.getAllByRole("textbox", { name: "Month" });
    const yearInputs = screen.getAllByRole("textbox", { name: "Year" });
    fireEvent.change(dayInputs[0], { target: { value: "" } });
    fireEvent.change(monthInputs[0], { target: { value: "" } });
    fireEvent.change(yearInputs[0], { target: { value: "" } });

    expect(onChange).toHaveBeenLastCalledWith(
      { benefit_start_date: null, employer_benefit_id: 0 },
      "amendedBenefits"
    );
  });

  it("restores original value on cancel, and minimizes form", () => {
    renderComponent({ isAddedByLeaveAdmin: false });
    userEvent.click(screen.getByRole("button", { name: "Amend" }));

    const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
      name: "Year",
    });
    fireEvent.change(startYearInput, { target: { value: "2020" } });
    fireEvent.change(endYearInput, { target: { value: "2020" } });
    expect(endYearInput).toHaveValue("2020");

    const cancelButton = screen.getByRole("button", {
      name: "Cancel amendment",
    });
    userEvent.click(cancelButton);
    expect(onChange).toHaveBeenLastCalledWith(
      employerBenefit,
      "amendedBenefits"
    );
    expect(screen.getByText("2/1/2021 to 3/1/2021")).toBeInTheDocument();
    expect(
      screen.queryByText(/Amend employer-sponsored benefit/)
    ).not.toBeInTheDocument();
  });

  it("for added benefits, form expanded by default (and no table row with the amend button)", () => {
    renderComponent();
    expect(
      screen.getByText(/Add an employer-sponsored benefit/)
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Amend" })
    ).not.toBeInTheDocument();
  });

  it("calls onRemove on cancel", () => {
    renderComponent({ isAddedByLeaveAdmin: true });
    const cancelButton = screen.getByRole("button", {
      name: "Cancel addition",
    });
    userEvent.click(cancelButton);
    expect(onRemove).toHaveBeenCalled();
  });

  it("benefit type is modifiable in v2", () => {
    renderComponent({ shouldShowV2: true });
    const benefitTypeRadio = screen.getByRole("radio", {
      name: "Permanent disability insurance",
    });
    userEvent.click(benefitTypeRadio);
    expect(onChange).toHaveBeenCalledWith(
      {
        benefit_type: EmployerBenefitType.permanentDisability,
        employer_benefit_id: 0,
      },
      "addedBenefits"
    );
  });

  it("full salary continuous is modifiable in v2", () => {
    renderComponent({ shouldShowV2: true });
    const salaryContinuousRadio = screen.getByRole("radio", { name: "No" });
    expect(salaryContinuousRadio).not.toBeChecked();
    userEvent.click(salaryContinuousRadio);
    expect(onChange).toHaveBeenCalledWith(
      { is_full_salary_continuous: false, employer_benefit_id: 0 },
      "addedBenefits"
    );
    expect(salaryContinuousRadio).toBeChecked();
  });
});
