import EmployerBenefit, {
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import OtherIncome, { OtherIncomeType } from "../../../src/models/OtherIncome";
import Review, {
  EmployerBenefitList,
  OtherIncomeList,
  OtherLeaveEntry,
  PreviousLeaveList,
} from "../../../src/pages/claims/review";
import { LeaveReason } from "../../../src/models/Claim";
import PreviousLeave from "../../../src/models/PreviousLeave";
import React from "react";
import { shallow } from "enzyme";

jest.mock("../../../src/hooks/useAppLogic");

describe("Part 1 Review Page", () => {
  describe("when all data is present", () => {
    it("renders Review page with Part 1 content and edit links", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockClaimBuilder().part1Complete().create(),
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data is empty", () => {
    it("does not render strings like 'null' or 'undefined'", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: {
          tax_identifier: "***-**-****",
          leave_details: {
            reason: LeaveReason.medical,
          },
        },
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  it("submits the application when the user clicks Submit", () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockClaimBuilder().part1Complete().create(),
    });
    wrapper.find("Button").simulate("click");

    expect(appLogic.claims.submit).toHaveBeenCalledWith(claim.application_id);
    expect(appLogic.claims.complete).not.toHaveBeenCalled();
  });
});

describe("Final Review Page", () => {
  describe("when all data is present", () => {
    it("renders Review page with final review page content and only edit links for Part 2/3 sections", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockClaimBuilder().complete().create(),
      });

      expect(wrapper).toMatchSnapshot();
      expect(
        wrapper
          .find("Trans[i18nKey='pages.claimsReview.partDescription']")
          .dive()
      ).toMatchSnapshot();
    });
  });

  it("completes the application when the user clicks Submit", () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockClaimBuilder().complete().create(),
    });
    wrapper.find("Button").simulate("click");

    expect(appLogic.claims.submit).not.toHaveBeenCalled();
    expect(appLogic.claims.complete).toHaveBeenCalledWith(claim.application_id);
  });
});

describe("Employer info", () => {
  describe("when claimant is not Employed", () => {
    it("does not render 'Notified employer' row or FEIN row", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockClaimBuilder().complete().create(),
      });

      expect(wrapper.text()).not.toContain("Notified employer");
      expect(wrapper.text()).not.toContain("Employer's FEIN");
    });
  });
});

describe("Duration type", () => {
  it("lists only existing duration type", () => {
    const intermittentClaim = new MockClaimBuilder()
      .part1Complete()
      .intermittent()
      .create();

    intermittentClaim.leave_details.continuous_leave_periods = [];

    const continuousAndReducedClaim = new MockClaimBuilder()
      .part1Complete()
      .continuous()
      .reducedSchedule()
      .create();

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
        level="4"
      >
        Intermittent leave
      </ReviewRow>
    `);
    expect(contAndReducedWrapper.find({ label: "Leave duration type" }))
      .toMatchInlineSnapshot(`
      <ReviewRow
        label="Leave duration type"
        level="4"
      >
        Continuous leave, Reduced leave schedule
      </ReviewRow>
    `);
  });
});

describe("Leave details", () => {
  const pregnancyOrRecentBirthLabel =
    "Are you pregnant or have you recently given birth?";
  const familyLeaveTypeLabel = "Family leave type";

  describe("When the reason is medical leave", () => {
    it("renders pregnancyOrRecentBirthLabel row", () => {
      const claim = new MockClaimBuilder().completed().create();
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: claim,
        render: "mount",
      });
      expect(wrapper.text()).toContain(pregnancyOrRecentBirthLabel);
      expect(wrapper.text()).not.toContain(familyLeaveTypeLabel);
    });
  });

  describe("When the reason is bonding leave", () => {
    it("renders family leave type row", () => {
      const claim = new MockClaimBuilder()
        .completed()
        .bondingBirthLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: claim,
        render: "mount",
      });
      expect(wrapper.text()).not.toContain(pregnancyOrRecentBirthLabel);
      expect(wrapper.text()).toContain(familyLeaveTypeLabel);
    });
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
      const wrapper = shallow(
        <EmployerBenefitList entries={entries} reviewRowLevel="4" />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [new EmployerBenefit()];
      const wrapper = shallow(
        <EmployerBenefitList entries={entries} reviewRowLevel="4" />
      );

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
      const wrapper = shallow(
        <OtherIncomeList entries={entries} reviewRowLevel="4" />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [new OtherIncome()];
      const wrapper = shallow(
        <OtherIncomeList entries={entries} reviewRowLevel="4" />
      );

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
      const wrapper = shallow(
        <PreviousLeaveList entries={entries} reviewRowLevel="4" />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [new PreviousLeave()];
      const wrapper = shallow(
        <PreviousLeaveList entries={entries} reviewRowLevel="4" />
      );

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
          reviewRowLevel="4"
        />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when data are missing", () => {
    it("doesn't render missing data", () => {
      const label = "Benefit 1";
      const wrapper = shallow(
        <OtherLeaveEntry
          label={label}
          type={null}
          dates=""
          amount={null}
          reviewRowLevel="4"
        />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });
});
