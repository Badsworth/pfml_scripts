import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
  WorkPatternType,
} from "../../../src/models/Claim";
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
import PreviousLeave from "../../../src/models/PreviousLeave";
import React from "react";
import { shallow } from "enzyme";

jest.mock("../../../src/hooks/useAppLogic");

// Dive more levels to account for withClaimDocuments HOC
const diveLevels = 4;

describe("Part 1 Review Page", () => {
  describe("when all data is present", () => {
    it("renders Review page with Part 1 content and edit links", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockClaimBuilder()
          .part1Complete()
          .mailingAddress()
          .create(),
        diveLevels,
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  it("does not render strings 'null', 'undefined', or missing translations", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockClaimBuilder().part1Complete().create(),
      diveLevels,
    });

    const html = wrapper.html();

    expect(html).not.toMatch("null");
    expect(html).not.toMatch("undefined");
    expect(html).not.toMatch("pages.claimsReview");
  });

  it("submits the application when the user clicks Submit", () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockClaimBuilder().part1Complete().create(),
      diveLevels,
    });
    wrapper.find("Button").simulate("click");

    expect(appLogic.claims.submit).toHaveBeenCalledWith(claim.application_id);
    expect(appLogic.claims.complete).not.toHaveBeenCalled();
  });
});

describe("Final Review Page", () => {
  let appLogic, claim, wrapper;
  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockClaimBuilder().complete().create(),
      diveLevels,
    }));
  });
  describe("when all data is present", () => {
    it("renders Review page with final review page content and only edit links for Part 2/3 sections", () => {
      expect(wrapper).toMatchSnapshot();
      expect(
        wrapper
          .find("Trans[i18nKey='pages.claimsReview.partDescription']")
          .dive()
      ).toMatchSnapshot();
    });
  });

  it("completes the application when the user clicks Submit", () => {
    wrapper.find("Button").simulate("click");

    expect(appLogic.claims.submit).not.toHaveBeenCalled();
    expect(appLogic.claims.complete).toHaveBeenCalledWith(claim.application_id);
  });

  it("renders a spinner for loading documents", () => {
    expect(wrapper.find("Spinner")).toHaveLength(1);
    expect(wrapper.exists({ label: "Number of files uploaded" })).toBe(false);
  });
});

describe("Work patterns", () => {
  it("has internationalized strings for each work pattern type", () => {
    expect.assertions();

    Object.values(WorkPatternType).forEach((work_pattern_type) => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockClaimBuilder()
          .part1Complete()
          .workPattern({ work_pattern_type })
          .create(),
        diveLevels,
      });

      expect(
        wrapper.find({ label: "Work schedule type" }).prop("children")
      ).toMatchSnapshot();
    });
  });
});

describe("Payment Information", () => {
  describe("When payment method is paper", () => {
    it("does not render 'Payment details' row", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockClaimBuilder().complete().check().create(),
        diveLevels,
      });
      expect(wrapper.find({ label: "Payment details" })).toHaveLength(0);
    });
  });
});

describe("Upload Document", () => {
  it("renders the correct number of documents", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockClaimBuilder().complete().create(),
      diveLevels,
      hasLoadedClaimDocuments: true,
    });
    expect(wrapper.exists("Spinner")).toBe(false);
    expect(wrapper.find({ label: "Number of files uploaded" })).toHaveLength(2);
  });

  it("renders Alert when there is an error for loading documents", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockClaimBuilder().complete().create(),
      diveLevels,
      hasLoadingDocumentsError: true,
    });

    expect(wrapper.exists("Alert")).toBe(true);
    expect(wrapper.exists({ label: "Number of files uploaded" })).toBe(false);
  });
});

describe("Employer info", () => {
  describe("when claimant is not Employed", () => {
    it("does not render 'Notified employer' row or FEIN row", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockClaimBuilder().complete().create(),
        diveLevels,
      });

      expect(wrapper.text()).not.toContain("Notified employer");
      expect(wrapper.text()).not.toContain("Employer's FEIN");
    });
  });
});

describe("Leave reason", () => {
  const pregnancyOrRecentBirthLabel = "Medical leave for pregnancy or birth";
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

describe("Intermittent leave frequency", () => {
  // Generate all possible combinations of Duration/Frequency for an Intermittent Leave Period:
  const durations = Object.values(DurationBasis);
  const frequencyIntervals = Object.values(FrequencyIntervalBasis);
  const intermittentLeavePeriodPermutations = [];

  durations.forEach((duration_basis) => {
    frequencyIntervals.forEach((frequency_interval_basis) => {
      intermittentLeavePeriodPermutations.push(
        new IntermittentLeavePeriod({
          duration_basis,
          frequency_interval_basis,
          frequency: 2,
          duration: 3,
        })
      );
    });

    intermittentLeavePeriodPermutations.push(
      new IntermittentLeavePeriod({
        duration_basis,
        frequency_interval: 6, // irregular over 6 months
        frequency_interval_basis: FrequencyIntervalBasis.months,
        frequency: 2,
        duration: 3,
      })
    );
  });

  it("renders the leave frequency and duration in plain language", () => {
    expect.assertions();

    intermittentLeavePeriodPermutations.forEach((intermittentLeavePeriod) => {
      const claim = new MockClaimBuilder().part1Complete().create();
      claim.leave_details.intermittent_leave_periods = [
        intermittentLeavePeriod,
      ];

      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: claim,
        diveLevels,
      });
      const contentElement = wrapper.find({
        i18nKey: "pages.claimsReview.intermittentFrequencyDuration",
      });

      expect(contentElement.dive()).toMatchSnapshot();
    });
  });

  it("does not render the intermittent leave frequency when a claim has no intermittent leave", () => {
    const claim = new MockClaimBuilder()
      .part1Complete({ excludeLeavePeriod: true })
      .create();

    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: claim,
    });
    const contentElement = wrapper.find({
      i18nKey: "pages.claimsReview.intermittentFrequencyDuration",
    });

    expect(contentElement.exists()).toBe(false);
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
