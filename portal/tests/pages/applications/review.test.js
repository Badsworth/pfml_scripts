import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../../src/models/BenefitsApplication";
import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
} from "../../test-utils";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../../src/models/OtherIncome";
import Review, {
  EmployerBenefitList,
  OtherIncomeList,
  OtherLeaveEntry,
} from "../../../src/pages/applications/review";
import { DateTime } from "luxon";
import { DocumentType } from "../../../src/models/Document";
import LeaveReason from "../../../src/models/LeaveReason";
import React from "react";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

// Dive more levels to account for withClaimDocuments HOC
const diveLevels = 4;

describe("Part 1 Review Page", () => {
  describe("when all data is present", () => {
    beforeEach(() => {
      mockRouter.pathname = routes.applications.review;
    });
    it("renders Review page with Part 1 content and edit links", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockBenefitsApplicationBuilder()
          .part1Complete()
          .mailingAddress()
          .fixedWorkPattern()
          .create(),
        diveLevels,
      });

      expect(wrapper).toMatchSnapshot();
    });
  });

  it("does not render strings 'null', 'undefined', or missing translations", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder().part1Complete().create(),
      diveLevels,
    });

    const html = wrapper.html();

    expect(html).not.toMatch("null");
    expect(html).not.toMatch("undefined");
    expect(html).not.toMatch("pages.claimsReview");
  });

  it("submits the application when the user clicks Submit", () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder().part1Complete().create(),
      diveLevels,
    });
    const submitSpy = jest.spyOn(appLogic.benefitsApplications, "submit");
    const completeSpy = jest.spyOn(appLogic.benefitsApplications, "complete");
    wrapper.find("Button").simulate("click");

    expect(submitSpy).toHaveBeenCalledWith(claim.application_id);
    expect(completeSpy).not.toHaveBeenCalled();
  });
});

describe("Final Review Page", () => {
  let appLogic, claim, wrapper;

  describe("when the claim is complete", () => {
    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockBenefitsApplicationBuilder().complete().create(),
        diveLevels,
      }));
    });

    it("renders Review page with final review page content and only edit links for Part 2/3 sections", () => {
      expect(wrapper).toMatchSnapshot();
      expect(
        wrapper
          .find("Trans[i18nKey='pages.claimsReview.partDescription']")
          .dive()
      ).toMatchSnapshot();
    });

    it("completes the application when the user clicks Submit", () => {
      const submitSpy = jest.spyOn(appLogic.benefitsApplications, "submit");
      const completeSpy = jest.spyOn(appLogic.benefitsApplications, "complete");
      wrapper.find("Button").simulate("click");

      expect(submitSpy).not.toHaveBeenCalled();
      expect(completeSpy).toHaveBeenCalledWith(claim.application_id);
    });

    it("renders a spinner for loading documents", () => {
      expect(wrapper.find("Spinner")).toHaveLength(1);
      expect(wrapper.exists({ label: "Number of files uploaded" })).toBe(false);
    });
  });

  it("conditionally renders Other Leave section based on presence of Yes/No fields", () => {
    const claimAttrs = new MockBenefitsApplicationBuilder().complete().create();
    claimAttrs.has_other_incomes = false;
    claimAttrs.has_employer_benefits = false;

    // Renders when false
    ({ wrapper } = renderWithAppLogic(Review, {
      claimAttrs,
      diveLevels,
    }));

    expect(wrapper.exists("[data-test='other-leave']")).toBe(true);

    // But doesn't render when null
    delete claimAttrs.has_other_incomes;
    delete claimAttrs.has_employer_benefits;

    ({ wrapper } = renderWithAppLogic(Review, {
      claimAttrs,
      diveLevels,
    }));

    expect(wrapper.exists("[data-test='other-leave']")).toBe(false);
  });
});

describe("Work patterns", () => {
  it("has internationalized strings for each work pattern type", () => {
    expect.assertions();

    ["Fixed", "Variable"].forEach((work_pattern_type) => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockBenefitsApplicationBuilder()
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

  it("shows work pattern days if work pattern type is fixed", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .part1Complete()
        .fixedWorkPattern()
        .create(),
      diveLevels,
    });

    expect(
      wrapper.find({ label: "Weekly work hours" }).prop("children")
    ).toMatchSnapshot();
    expect(wrapper.find({ label: "Average weekly hours" }).exists()).toBe(
      false
    );
  });

  it("shows average weekly hours if work pattern type is variable", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .part1Complete()
        .variableWorkPattern()
        .create(),
      diveLevels,
    });

    expect(
      wrapper.find({ label: "Average weekly hours" }).prop("children")
    ).toMatchSnapshot();
    expect(wrapper.find({ label: "Weekly work hours" }).exists()).toBe(false);
  });
});

describe("Payment Information", () => {
  describe("When payment method is paper", () => {
    it("does not render 'Payment details' row", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockBenefitsApplicationBuilder()
          .complete()
          .check()
          .create(),
        diveLevels,
      });
      expect(wrapper.find({ label: "Payment details" })).toHaveLength(0);
    });
  });
});

describe("Upload Document", () => {
  it("renders the correct number of certification documents when there are no documents", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder().complete().create(),
      diveLevels,
      hasLoadedClaimDocuments: true,
    });

    expect(wrapper.exists("Spinner")).toBe(false);
    expect(wrapper.find("[data-test='certification-doc-count']"))
      .toMatchInlineSnapshot(`
      <ReviewRow
        data-test="certification-doc-count"
        label="Number of files uploaded"
        level="3"
      >
        0
      </ReviewRow>
    `);
  });

  it("renders filtered documents when the document type matches the leave reason with Caring Leave feature flag enabled", () => {
    // When the feature flag is enabled, the component should render the number of documents with a DocType that match the leave reason
    // In this test case, the feature flag is enabled, and the claim has documents with DocTypes that match the leave reason,
    // so the component should render 3 documents attached

    // create a claim with matching leave reason and doc types
    process.env.featureFlags = {
      showCaringLeaveType: true,
    };

    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .complete()
        .create(),
      diveLevels,
      hasLoadedClaimDocuments: true,
      hasUploadedCertificationDocuments: {
        document_type: DocumentType.certification[LeaveReason.medical],
        numberOfDocs: 3,
      },
    });

    expect(wrapper.exists("Spinner")).toBe(false);
    expect(wrapper.find("[data-test='certification-doc-count']"))
      .toMatchInlineSnapshot(`
      <ReviewRow
        data-test="certification-doc-count"
        label="Number of files uploaded"
        level="3"
      >
        3
      </ReviewRow>
    `);
  });

  it("renders filtered documents when the document type doesn't match the leave reason when the caring leave feature flag is enabled", () => {
    // When the feature flag is enabled, the component should render the number of documents with a DocType that match the leave reason
    // In this test case, the feature flag is enabled, and the claim has documents with DocTypes that don't match the leave reason,
    // so the component should render 0 documents attached
    process.env.featureFlags = {
      showCaringLeaveType: true,
    };

    // create a claim with mismatched leave reason and doc types
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .medicalLeaveReason()
        .complete()
        .create(),
      diveLevels,
      hasLoadedClaimDocuments: true,
      hasUploadedCertificationDocuments: {
        document_type: DocumentType.certification[LeaveReason.bonding],
        numberOfDocs: 2,
      },
    });

    expect(wrapper.exists("Spinner")).toBe(false);
    expect(wrapper.find("[data-test='certification-doc-count']"))
      .toMatchInlineSnapshot(`
      <ReviewRow
        data-test="certification-doc-count"
        label="Number of files uploaded"
        level="3"
      >
        0
      </ReviewRow>
    `);
  });

  it("renders Alert when there is an error for loading documents", () => {
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder().complete().create(),
      diveLevels,
      hasLoadingDocumentsError: true,
    });

    expect(wrapper.exists("Alert")).toBe(true);
    expect(wrapper.exists({ label: "Number of files uploaded" })).toBe(false);
  });

  it("does not render certification document for bonding leave in advance", () => {
    const futureDate = DateTime.local().plus({ months: 1 }).toISODate();
    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .complete()
        .bondingBirthLeaveReason(futureDate)
        .hasFutureChild()
        .create(),
      diveLevels,
      hasLoadedClaimDocuments: true,
    });
    expect(wrapper.find({ label: "Number of files uploaded" })).toHaveLength(1);
  });
});

describe("Employer info", () => {
  describe("when claimant is not Employed", () => {
    it("does not render 'Notified employer' row or FEIN row", () => {
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: new MockBenefitsApplicationBuilder().complete().create(),
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
      const claim = new MockBenefitsApplicationBuilder().completed().create();
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: claim,
        diveLevels,
      });
      expect(
        wrapper.find({ label: pregnancyOrRecentBirthLabel }).exists()
      ).toBe(true);
      expect(wrapper.find({ label: familyLeaveTypeLabel }).exists()).toBe(
        false
      );
    });
  });

  describe("When the reason is bonding leave", () => {
    it("renders family leave type row", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .completed()
        .bondingBirthLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: claim,
        diveLevels,
      });
      expect(
        wrapper.find({ label: pregnancyOrRecentBirthLabel }).exists()
      ).toBe(false);
      expect(wrapper.find({ label: familyLeaveTypeLabel }).exists()).toBe(true);
    });
  });

  describe("When the reason is caring leave", () => {
    it("renders caring leave details", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .completed()
        .caringLeaveReason()
        .create();
      const { wrapper } = renderWithAppLogic(Review, {
        claimAttrs: claim,
        diveLevels,
      });
      expect(wrapper).toMatchSnapshot();
    });
  });
});

describe("Reduced leave", () => {
  it("renders WeeklyTimeTable for the reduced leave period when work pattern is Fixed", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .part1Complete()
      .fixedWorkPattern()
      .reducedSchedule()
      .create();

    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: claim,
      diveLevels,
    });

    expect(wrapper.find({ label: "Hours off per week" })).toMatchSnapshot();
  });

  it("renders total time for the reduced leave period when work pattern is Variable", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .part1Complete()
      .variableWorkPattern()
      .reducedSchedule()
      .create();

    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: claim,
      diveLevels,
    });

    expect(wrapper.find({ label: "Hours off per week" })).toMatchSnapshot();
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
      const claim = new MockBenefitsApplicationBuilder()
        .part1Complete()
        .create();
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
    const claim = new MockBenefitsApplicationBuilder()
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
      benefit_amount_frequency: EmployerBenefitFrequency.monthly,
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.paidLeave,
    }),
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_amount_frequency: EmployerBenefitFrequency.monthly,
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.shortTermDisability,
    }),
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_amount_frequency: EmployerBenefitFrequency.monthly,
      benefit_end_date: "2021-12-30",
      benefit_start_date: "2021-08-12",
      benefit_type: EmployerBenefitType.permanentDisability,
    }),
    new EmployerBenefit({
      benefit_amount_dollars: "250",
      benefit_amount_frequency: EmployerBenefitFrequency.monthly,
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

  describe("when amount fields are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [
        new EmployerBenefit({
          benefit_end_date: "2021-12-30",
          benefit_start_date: "2021-08-12",
          benefit_type: EmployerBenefitType.permanentDisability,
        }),
      ];
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
          income_amount_frequency: OtherIncomeFrequency.monthly,
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.workersCompensation,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_amount_frequency: OtherIncomeFrequency.monthly,
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.unemployment,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_amount_frequency: OtherIncomeFrequency.monthly,
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.ssdi,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_amount_frequency: OtherIncomeFrequency.monthly,
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.retirementDisability,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_amount_frequency: OtherIncomeFrequency.monthly,
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.jonesAct,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_amount_frequency: OtherIncomeFrequency.monthly,
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.railroadRetirement,
        }),
        new OtherIncome({
          income_amount_dollars: "250",
          income_amount_frequency: OtherIncomeFrequency.monthly,
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.otherEmployer,
        }),
      ];
      const wrapper = shallow(
        <OtherIncomeList entries={entries} reviewRowLevel="4" />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when amount fields are missing", () => {
    it("doesn't render missing data", () => {
      const entries = [
        new OtherIncome({
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.otherEmployer,
        }),
      ];
      const wrapper = shallow(
        <OtherIncomeList entries={entries} reviewRowLevel="4" />
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

  describe("when amount is missing", () => {
    it("doesn't render missing data", () => {
      const label = "Benefit 1";
      const type = "Medical or family leave";
      const dates = "07-22-2020 - 09-22-2020";
      const wrapper = shallow(
        <OtherLeaveEntry
          label={label}
          type={type}
          dates={dates}
          amount={null}
          reviewRowLevel="4"
        />
      );

      expect(wrapper).toMatchSnapshot();
    });
  });
});

describe("CaringLeave", () => {
  it("renders family member's relationship", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .part1Complete()
      .caringLeaveReason()
      .create();

    const { wrapper } = renderWithAppLogic(Review, {
      claimAttrs: claim,
      diveLevels,
    });

    expect(
      wrapper.find({ label: "Family member's relationship" })
    ).toMatchSnapshot();
  });
});
