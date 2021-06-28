/* eslint-disable import/first */
jest.mock("../../../src/hooks/useAppLogic");

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

import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import Review, {
  EmployerBenefitList,
  OtherIncomeList,
  OtherLeaveEntry,
  PreviousLeaveList,
} from "../../../src/pages/applications/review";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import { DateTime } from "luxon";
import { DocumentType } from "../../../src/models/Document";
import LeaveReason from "../../../src/models/LeaveReason";
import React from "react";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { shallow } from "enzyme";
import { times } from "lodash";
import useAppLogic from "../../../src/hooks/useAppLogic";
import usePortalFlow from "../../../src/hooks/usePortalFlow";

const setup = (options = {}) => {
  // Set the correct initial path so that generated URLs are correct
  mockRouter.pathname = routes.applications.review;

  options = {
    claimAttrs: new MockBenefitsApplicationBuilder().part1Complete().create(),
    // Dive more levels to account for withClaimDocuments HOC
    diveLevels: 4,
    ...options,
  };
  const { appLogic, claim, wrapper } = renderWithAppLogic(Review, options);

  return { appLogic, claim, wrapper };
};

describe("Review Page", () => {
  beforeAll(() => {
    // Mock app logic to avoid cognito errors but use the real
    // usePortalFlow() hook so that the URLs rendered on the page are correct
    const appLogic = useAppLogic();
    useAppLogic.mockImplementation(() => ({
      ...appLogic,
      portalFlow: usePortalFlow(),
    }));
  });

  describe("Part 1 Review Page", () => {
    describe("when all data is present", () => {
      it("renders Review page with Part 1 content and edit links", () => {
        const { wrapper } = setup({
          claimAttrs: new MockBenefitsApplicationBuilder()
            .part1Complete()
            .mailingAddress()
            .fixedWorkPattern()
            .previousLeavesSameReason()
            .previousLeavesOtherReason()
            .concurrentLeave()
            .otherIncome()
            .employerBenefit()
            .create(),
        });

        expect(wrapper).toMatchSnapshot();
      });
    });

    it("does not render strings 'null', 'undefined', or missing translations", () => {
      const { wrapper } = setup();

      const html = wrapper.html();

      expect(html).not.toMatch("null");
      expect(html).not.toMatch("undefined");
      expect(html).not.toMatch("pages.claimsReview");
    });

    it("submits the application when the user clicks Submit", () => {
      const { appLogic, claim, wrapper } = setup();
      const submitSpy = jest.spyOn(appLogic.benefitsApplications, "submit");
      const completeSpy = jest.spyOn(appLogic.benefitsApplications, "complete");
      wrapper.find("Button").simulate("click");

      expect(submitSpy).toHaveBeenCalledWith(claim.application_id);
      expect(completeSpy).not.toHaveBeenCalled();
    });

    it("renders a custom Alert when there are missing required fields", () => {
      const appErrors = new AppErrorInfoCollection([
        new AppErrorInfo({ type: "required" }),
      ]);
      const root = setup({ render: "mount", diveLevels: 0 }).wrapper;
      let wrapper = root;
      times(4, () => (wrapper = wrapper.childAt(0)));

      expect(wrapper.exists("Alert")).toBe(false);
      act(() => {
        // Simulate missing required field errors
        const appLogic = root.props().appLogic;
        root.setProps({
          appLogic: {
            ...appLogic,
            appErrors,
          },
        });
      });
      root.update();
      wrapper = root;
      times(4, () => (wrapper = wrapper.childAt(0)));

      expect(wrapper.exists("Alert")).toBe(true);
      const alert = wrapper.find("Alert");
      expect(alert).toMatchSnapshot();
    });
  });

  describe("Final Review Page", () => {
    describe("when the claim is complete", () => {
      const claimAttrs = new MockBenefitsApplicationBuilder()
        .complete()
        .create();

      it("renders Review page with final review page content and only edit links for Part 2/3 sections", () => {
        const { wrapper } = setup({ claimAttrs });
        expect(wrapper).toMatchSnapshot();
        expect(
          wrapper
            .find("Trans[i18nKey='pages.claimsReview.partDescription']")
            .dive()
        ).toMatchSnapshot();
      });

      it("completes the application when the user clicks Submit", () => {
        const { appLogic, claim, wrapper } = setup({ claimAttrs });
        const submitSpy = jest.spyOn(appLogic.benefitsApplications, "submit");
        const completeSpy = jest.spyOn(
          appLogic.benefitsApplications,
          "complete"
        );
        wrapper.find("Button").simulate("click");

        expect(submitSpy).not.toHaveBeenCalled();
        expect(completeSpy).toHaveBeenCalledWith(claim.application_id);
      });

      it("renders a spinner for loading documents", () => {
        const { wrapper } = setup({ claimAttrs });
        expect(wrapper.find("Spinner")).toHaveLength(1);
        expect(wrapper.exists({ label: "Number of files uploaded" })).toBe(
          false
        );
      });
    });

    it("conditionally renders Other Leave section based on presence of Yes/No fields", () => {
      const claimAttrs = new MockBenefitsApplicationBuilder()
        .complete()
        .create();
      claimAttrs.has_other_incomes = false;
      claimAttrs.has_employer_benefits = false;
      let wrapper;

      // Renders when false
      ({ wrapper } = setup({
        claimAttrs,
      }));

      expect(wrapper.exists("[data-test='other-leave']")).toBe(true);

      // But doesn't render when null
      delete claimAttrs.has_other_incomes;
      delete claimAttrs.has_employer_benefits;
      delete claimAttrs.has_previous_leaves_same_reason;
      delete claimAttrs.has_previous_leaves_other_reason;
      delete claimAttrs.has_concurrent_leave;

      ({ wrapper } = setup({
        claimAttrs,
      }));

      expect(wrapper.exists("[data-test='other-leave']")).toBe(false);
    });
  });

  describe("Work patterns", () => {
    it("has internationalized strings for each work pattern type", () => {
      expect.assertions();

      ["Fixed", "Variable"].forEach((work_pattern_type) => {
        const { wrapper } = setup({
          claimAttrs: new MockBenefitsApplicationBuilder()
            .part1Complete()
            .workPattern({ work_pattern_type })
            .create(),
        });

        expect(
          wrapper.find({ label: "Work schedule type" }).prop("children")
        ).toMatchSnapshot();
      });
    });

    it("shows work pattern days if work pattern type is fixed", () => {
      const { wrapper } = setup({
        claimAttrs: new MockBenefitsApplicationBuilder()
          .part1Complete()
          .fixedWorkPattern()
          .create(),
      });

      expect(
        wrapper.find({ label: "Weekly work hours" }).prop("children")
      ).toMatchSnapshot();
      expect(wrapper.find({ label: "Average weekly hours" }).exists()).toBe(
        false
      );
    });

    it("shows average weekly hours if work pattern type is variable", () => {
      const { wrapper } = setup({
        claimAttrs: new MockBenefitsApplicationBuilder()
          .part1Complete()
          .variableWorkPattern()
          .create(),
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
        const { wrapper } = setup({
          claimAttrs: new MockBenefitsApplicationBuilder()
            .complete()
            .check()
            .create(),
        });
        expect(wrapper.find({ label: "Payment details" })).toHaveLength(0);
      });
    });
  });

  describe("Upload Document", () => {
    it("renders the correct number of certification documents when there are no documents", () => {
      const { wrapper } = setup({
        claimAttrs: new MockBenefitsApplicationBuilder().complete().create(),
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

    it("renders filtered documents when the document type matches the leave reason with useNewPlanProofs flag enabled", () => {
      // When the feature flag is enabled, the component should render the number of documents with a DocType that match the leave reason
      // In this test case, the feature flag is enabled, and the claim has documents with DocTypes that match the leave reason,
      // so the component should render 3 documents attached
      // TODO (CP-2306): Remove or disable useNewPlanProofs feature flag to coincide with FINEOS 6/25 udpate

      // create a claim with matching leave reason and doc types
      process.env.featureFlags = {
        useNewPlanProofs: true,
      };

      const { wrapper } = setup({
        claimAttrs: new MockBenefitsApplicationBuilder()
          .medicalLeaveReason()
          .complete()
          .create(),
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

    it("renders filtered documents when the document type doesn't match the leave reason when the useNewPlanProofs feature flag is enabled", () => {
      // When the feature flag is enabled, the component should render the number of documents with a DocType that match the leave reason
      // In this test case, the feature flag is enabled, and the claim has documents with DocTypes that don't match the leave reason,
      // so the component should render 0 documents attached
      // TODO (CP-2306): Remove or disable useNewPlanProofs feature flag to coincide with FINEOS 6/25 udpate

      process.env.featureFlags = {
        useNewPlanProofs: true,
      };

      // create a claim with mismatched leave reason and doc types
      const { wrapper } = setup({
        claimAttrs: new MockBenefitsApplicationBuilder()
          .medicalLeaveReason()
          .complete()
          .create(),
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
        3
      </ReviewRow>
    `);
    });

    it("renders Alert when there is an error for loading documents", () => {
      const { wrapper } = setup({
        claimAttrs: new MockBenefitsApplicationBuilder().complete().create(),
        hasLoadingDocumentsError: true,
      });

      expect(wrapper.exists("Alert")).toBe(true);
      expect(wrapper.exists({ label: "Number of files uploaded" })).toBe(false);
    });

    it("does not render certification document for bonding leave in advance", () => {
      const futureDate = DateTime.local().plus({ months: 1 }).toISODate();
      const { wrapper } = setup({
        claimAttrs: new MockBenefitsApplicationBuilder()
          .complete()
          .bondingBirthLeaveReason(futureDate)
          .hasFutureChild()
          .create(),
        hasLoadedClaimDocuments: true,
      });
      expect(wrapper.find({ label: "Number of files uploaded" })).toHaveLength(
        1
      );
    });
  });

  describe("Employer info", () => {
    describe("when claimant is not Employed", () => {
      it("does not render 'Notified employer' row or FEIN row", () => {
        const { wrapper } = setup({
          claimAttrs: new MockBenefitsApplicationBuilder().complete().create(),
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
        const { wrapper } = setup({
          claimAttrs: claim,
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
        const { wrapper } = setup({
          claimAttrs: claim,
        });
        expect(
          wrapper.find({ label: pregnancyOrRecentBirthLabel }).exists()
        ).toBe(false);
        expect(wrapper.find({ label: familyLeaveTypeLabel }).exists()).toBe(
          true
        );
      });
    });

    describe("When the reason is caring leave", () => {
      it("renders caring leave details", () => {
        const claim = new MockBenefitsApplicationBuilder()
          .completed()
          .caringLeaveReason()
          .create();
        const { wrapper } = setup({
          claimAttrs: claim,
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

      const { wrapper } = setup({
        claimAttrs: claim,
      });

      expect(wrapper.find({ label: "Hours off per week" })).toMatchSnapshot();
    });

    it("renders total time for the reduced leave period when work pattern is Variable", () => {
      const claim = new MockBenefitsApplicationBuilder()
        .part1Complete()
        .variableWorkPattern()
        .reducedSchedule()
        .create();

      const { wrapper } = setup({
        claimAttrs: claim,
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

        const { wrapper } = setup({
          claimAttrs: claim,
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
        is_full_salary_continuous: false,
      }),
      new EmployerBenefit({
        benefit_amount_dollars: "250",
        benefit_amount_frequency: EmployerBenefitFrequency.monthly,
        benefit_end_date: "2021-12-30",
        benefit_start_date: "2021-08-12",
        benefit_type: EmployerBenefitType.shortTermDisability,
        is_full_salary_continuous: false,
      }),
      new EmployerBenefit({
        benefit_amount_dollars: "250",
        benefit_amount_frequency: EmployerBenefitFrequency.monthly,
        benefit_end_date: "2021-12-30",
        benefit_start_date: "2021-08-12",
        benefit_type: EmployerBenefitType.permanentDisability,
        is_full_salary_continuous: true,
      }),
      new EmployerBenefit({
        benefit_amount_dollars: "250",
        benefit_amount_frequency: EmployerBenefitFrequency.monthly,
        benefit_end_date: "2021-12-30",
        benefit_start_date: "2021-08-12",
        benefit_type: EmployerBenefitType.familyOrMedicalLeave,
        is_full_salary_continuous: true,
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

  describe("PreviousLeaveList", () => {
    it("renders other reason list", () => {
      const entries = [
        new PreviousLeave({
          is_for_current_employer: true,
          leave_end_date: "2021-05-01",
          leave_start_date: "2021-07-01",
          leave_minutes: 20 * 60,
          leave_reason: PreviousLeaveReason.care,
          worked_per_week_minutes: 40 * 60,
        }),
        new PreviousLeave({
          is_for_current_employer: false,
          leave_end_date: "2021-05-01",
          leave_start_date: "2021-07-01",
          leave_minutes: 20 * 60,
          leave_reason: PreviousLeaveReason.bonding,
          worked_per_week_minutes: 40 * 60,
        }),
      ];

      const wrapper = shallow(
        <PreviousLeaveList
          entries={entries}
          type="otherReason"
          startIndex={1}
          reviewRowLevel="4"
        />
      );

      expect(wrapper).toMatchSnapshot();
    });

    it("renders same reason list", () => {
      const entries = [
        new PreviousLeave({
          is_for_current_employer: true,
          leave_end_date: "2021-05-01",
          leave_start_date: "2021-07-01",
          leave_minutes: 20 * 60,
          leave_reason: null,
          worked_per_week_minutes: 40 * 60,
        }),
        new PreviousLeave({
          is_for_current_employer: false,
          leave_end_date: "2021-05-01",
          leave_start_date: "2021-07-01",
          leave_minutes: 20 * 60,
          leave_reason: null,
          worked_per_week_minutes: 40 * 60,
        }),
      ];

      const wrapper = shallow(
        <PreviousLeaveList
          entries={entries}
          type="sameReason"
          startIndex={1}
          reviewRowLevel="4"
        />
      );

      expect(wrapper).toMatchSnapshot();
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

      const { wrapper } = setup({
        claimAttrs: claim,
      });

      expect(
        wrapper.find({ label: "Family member's relationship" })
      ).toMatchSnapshot();
    });
  });
});
