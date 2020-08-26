import {
  ContinuousLeavePeriod,
  EmploymentStatus,
  IntermittentLeavePeriod,
  LeaveReason,
  PaymentPreferenceMethod,
  ReducedScheduleLeavePeriod,
} from "../../../src/models/Claim";
import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import OtherIncome, { OtherIncomeType } from "../../../src/models/OtherIncome";
import Review, {
  EmployerBenefitList,
  OtherIncomeList,
  OtherLeaveEntry,
  PreviousLeaveList,
} from "../../../src/pages/claims/review";
import PreviousLeave from "../../../src/models/PreviousLeave";
import React from "react";
import { renderWithAppLogic } from "../../test-utils";
import { shallow } from "enzyme";

/**
 * Get a claim for an Employed claimant, with all required fields.
 * Fields can be overridden in each unit test.
 * @returns {object}
 */
function fullClaimAttrs() {
  const employer_benefits = [
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.paidLeave,
    }),
  ];

  const other_incomes = [
    new OtherIncome({
      income_amount_dollars: "250",
      income_end_date: "2021-12-30",
      income_start_date: "2021-08-12",
      income_type: OtherIncomeType.workersCompensation,
    }),
  ];

  const previous_leaves = [
    new PreviousLeave({
      leave_end_date: "2021-12-30",
      leave_start_date: "2021-08-12",
    }),
  ];

  return {
    employer_benefits,
    employment_status: EmploymentStatus.employed,
    employer_fein: "12-1234567",
    first_name: "Bud",
    has_employer_benefits: true,
    has_other_incomes: true,
    has_previous_leaves: true,
    has_state_id: true,
    last_name: "Baxter",
    leave_details: {
      employer_notified: true,
      employer_notification_date: "2020-06-25",
      intermittent_leave_periods: [new IntermittentLeavePeriod()],
      reason: LeaveReason.medical,
    },
    mass_id: "*********",
    middle_name: "Monstera",
    other_incomes,
    previous_leaves,
    temp: {
      leave_details: {
        avg_weekly_work_hours: "20",
        continuous_leave_periods: [new ContinuousLeavePeriod()],
        end_date: "2021-12-30",
        reduced_schedule_leave_periods: [new ReducedScheduleLeavePeriod()],
        start_date: "2021-09-21",
      },
      payment_preferences: [{ payment_method: PaymentPreferenceMethod.ach }],
      residential_address: {
        city: "Boston",
        line_1: "19 Staniford St",
        line_2: "Suite 505",
        state: "MA",
        zip: "02114",
      },
    },
  };
}

describe("Review", () => {
  describe("when all data is present", () => {
    it("renders Review page with the field values", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: fullClaimAttrs(),
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when claimant is not Employed", () => {
    it("does not render 'Notified employer' row or FEIN row", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: fullClaimAttrs(),
      });

      expect(wrapper.text()).not.toContain("Notified employer");
      expect(wrapper.text()).not.toContain("Employer's FEIN");
    });
  });

  describe("when data is empty", () => {
    it("does not render strings like 'null' or 'undefined'", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: {
          leave_details: {
            reason: LeaveReason.medical,
          },
        },
      });

      expect(wrapper).toMatchSnapshot();
    });
  });
});

describe("Duration type", () => {
  it("lists only existing duration type", () => {
    const intermittentClaim = {
      leave_details: {
        intermittent_leave_periods: [new IntermittentLeavePeriod()],
      },
    };

    const continuousAndReducedClaim = {
      temp: {
        leave_details: {
          continuous_leave_periods: [new ContinuousLeavePeriod()],
          reduced_schedule_leave_periods: [new ReducedScheduleLeavePeriod()],
        },
        // TODO CP-744: remove once BaseModel merges properties
        payment_preferences: [{}],
      },
    };

    const { wrapper: intermittentWrapper } = renderWithAppLogic(Review, {
      claimAttrs: intermittentClaim,
    });
    const { wrapper: contAndReducedWrapper } = renderWithAppLogic(Review, {
      claimAttrs: continuousAndReducedClaim,
    });

    expect(intermittentWrapper.find({ label: "Leave duration type" }))
      .toMatchInlineSnapshot(`
      <ReviewRow
        label="Leave duration type"
      >
        Intermittent leave
      </ReviewRow>
    `);
    expect(contAndReducedWrapper.find({ label: "Leave duration type" }))
      .toMatchInlineSnapshot(`
      <ReviewRow
        label="Leave duration type"
      >
        Continuous leave, Reduced leave schedule
      </ReviewRow>
    `);
  });
});

describe("EmployerBenefitList", () => {
  const entries = [
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.paidLeave,
    }),
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.shortTermDisability,
    }),
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.permanentDisability,
    }),
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.familyOrMedicalLeave,
    }),
  ];

  describe("when all data are present", () => {
    it("renders all data fields", () => {
      const wrapper = shallow(<EmployerBenefitList entries={entries} />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [new EmployerBenefit()];
      const wrapper = shallow(<EmployerBenefitList entries={entries} />);

      expect(wrapper).toMatchSnapshot();
    });
  });
});

describe("OtherIncomeList", () => {
  describe("when all data are present", () => {
    it("renders all data fields", () => {
      const entries = [
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.workersCompensation,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.unemployment,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.ssdi,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.retirementDisability,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.jonesAct,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.railroadRetirement,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.otherEmployer,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.selfEmployment,
        }),
      ];
      const wrapper = shallow(<OtherIncomeList entries={entries} />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [new OtherIncome()];
      const wrapper = shallow(<OtherIncomeList entries={entries} />);

      expect(wrapper).toMatchSnapshot();
    });
  });
});

describe("PreviousLeaveList", () => {
  describe("when all data are present", () => {
    it("renders all data fields", () => {
      const entries = [
        new PreviousLeave({
          leave_end_date: "2021-12-30",
          leave_start_date: "2021-08-12",
        }),
      ];
      const wrapper = shallow(<PreviousLeaveList entries={entries} />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [new PreviousLeave()];
      const wrapper = shallow(<PreviousLeaveList entries={entries} />);

      expect(wrapper).toMatchSnapshot();
    });
  });
});

describe("OtherLeaveEntry", () => {
  describe("when all data are present", () => {
    it("renders all data fields", () => {
      const label = "Benefit 1";
      const type = "Medical or family leave";
      const dates = "07-22-2020 - 09-22-2020";
      const amount = "$250 per month";
      const wrapper = shallow(
        <OtherLeaveEntry
          label={label}
          type={type}
          dates={dates}
          amount={amount}
        />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const label = "Benefit 1";
      const wrapper = shallow(
        <OtherLeaveEntry label={label} type={null} dates="" amount={null} />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });
});
