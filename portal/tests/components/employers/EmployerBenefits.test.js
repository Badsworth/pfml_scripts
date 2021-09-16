import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import { render, screen } from "@testing-library/react";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import EmployerBenefits from "../../../src/components/employers/EmployerBenefits";
import React from "react";

const BENEFITS = [
  new EmployerBenefit({
    benefit_amount_dollars: 1000,
    benefit_amount_frequency: EmployerBenefitFrequency.weekly,
    benefit_end_date: "2021-03-01",
    benefit_start_date: "2021-02-01",
    benefit_type: EmployerBenefitType.shortTermDisability,
    employer_benefit_id: 0,
    is_full_salary_continuous: false,
  }),
  new EmployerBenefit({
    benefit_amount_dollars: 2000,
    benefit_amount_frequency: EmployerBenefitFrequency.weekly,
    benefit_end_date: "2021-05-11",
    benefit_start_date: "2021-05-01",
    benefit_type: EmployerBenefitType.paidLeave,
    employer_benefit_id: 1,
    is_full_salary_continuous: true,
  }),
];

function renderComponent(customProps) {
  const props = {
    addedBenefits: [],
    appErrors: new AppErrorInfoCollection(),
    employerBenefits: BENEFITS,
    onAdd: () => {},
    onChange: () => {},
    onRemove: () => {},
    shouldShowV2: false,
    ...customProps,
  };

  return render(<EmployerBenefits {...props} />);
}

describe("EmployerBenefits", () => {
  it("renders the component for v1 eforms", () => {
    const { container } = renderComponent();
    expect(container).toMatchSnapshot();
  });

  it("renders the component for v2 eforms", () => {
    const { container } = renderComponent({
      shouldShowV2: true,
    });
    expect(container).toMatchSnapshot();
  });

  it("displays 'None reported' if no benefits are reported", () => {
    renderComponent({ employerBenefits: [] });

    expect(
      screen.getByRole("cell", { name: /None reported/i })
    ).toBeInTheDocument();
  });

  it('displays a row for each benefit in "employerBenefits"', () => {
    renderComponent();

    expect(screen.queryAllByTestId("benefit-details-row")).toHaveLength(
      BENEFITS.length
    );
  });

  describe("when 'shouldShowV2' is true", () => {
    it("displays rows for added benefits", () => {
      renderComponent({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: true,
      });

      expect(screen.queryAllByTestId("added-benefit-details-row")).toHaveLength(
        BENEFITS.length
      );
    });

    it("displays the first 'Add benefit' button when there are no benefits added", () => {
      renderComponent({
        employerBenefits: [],
        shouldShowV2: true,
      });

      expect(
        screen.getByRole("button", {
          name: "Add an employer-sponsored benefit",
        })
      ).toBeInTheDocument();
    });

    it("displays the subsequent 'Add benefit' button when there are benefits added", () => {
      renderComponent({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: true,
      });

      expect(
        screen.getByRole("button", {
          name: "Add another employer-sponsored benefit",
        })
      ).toBeInTheDocument();
    });
  });

  describe("when 'shouldShowV2' is false", () => {
    it("does not display rows for added benefits", () => {
      renderComponent({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: false,
      });

      expect(screen.queryAllByTestId("added-benefit-details-row")).toHaveLength(
        0
      );
    });

    it("does not display the 'Add benefit' button", () => {
      renderComponent({
        addedBenefits: BENEFITS,
        employerBenefits: [],
        shouldShowV2: false,
      });

      expect(screen.queryByRole("button")).not.toBeInTheDocument();
    });
  });
});
