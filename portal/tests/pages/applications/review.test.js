import Document, { DocumentType } from "../../../src/models/Document";
import {
  DurationBasis,
  EmploymentStatus,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../../src/models/BenefitsApplication";
import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../../src/models/EmployerBenefit";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../../src/models/OtherIncome";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../../../src/models/PreviousLeave";
import React, { useEffect } from "react";
import Review, {
  EmployerBenefitList,
  OtherIncomeList,
  OtherLeaveEntry,
  PreviousLeaveList,
} from "../../../src/pages/applications/review";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import { DateTime } from "luxon";
import DocumentCollection from "../../../src/models/DocumentCollection";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = ({ appErrors, claim, documents } = {}) => {
  // Set the correct initial path so that generated URLs are correct
  mockRouter.pathname = routes.applications.review;

  if (!claim) {
    claim = new MockBenefitsApplicationBuilder().part1Complete().create();
  }

  let completeSpy, submitSpy;
  const utils = renderPage(
    Review,
    {
      addCustomSetup: (appLogic) => {
        submitSpy = jest.spyOn(appLogic.benefitsApplications, "submit");
        completeSpy = jest.spyOn(appLogic.benefitsApplications, "complete");

        // Mock the Application
        setupBenefitsApplications(appLogic, [claim]);

        // Mock the Application's documents
        appLogic.documents.documents = new DocumentCollection(documents);
        jest
          .spyOn(appLogic.documents, "hasLoadedClaimDocuments")
          .mockReturnValue(true);

        if (appErrors) {
          // Rather than mutating the appErrors, we set them as they would
          // when the API request completes. This fixes an issue where mutating
          // appLogic.appErrors was causing an infinite loop in our tests.
          // eslint-disable-next-line react-hooks/rules-of-hooks
          useEffect(() => {
            appLogic.setAppErrors(appErrors);
          });
        }
      },
    },
    { query: { claim_id: claim.application_id } }
  );

  return { completeSpy, submitSpy, ...utils };
};

describe("Review Page", () => {
  it("renders Review page with Part 1 content and edit links when application hasn't been submitted yet", () => {
    const { container } = setup({
      claim: new MockBenefitsApplicationBuilder()
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

    expect(container).toMatchSnapshot();

    // Safeguard to ensure we're passing in all the required data into our test.
    // There shouldn't be any missing content strings.
    expect(screen.queryByText(/pages\.claimsReview/i)).not.toBeInTheDocument();
  });

  it("renders Review page with all sections and only edit links for Part 3 sections when Part 1 has already been submitted", () => {
    const { container } = setup({
      claim: new MockBenefitsApplicationBuilder().complete().create(),
    });

    expect(container).toMatchSnapshot();

    // Safeguard to ensure we're passing in all the required data into our test.
    // There shouldn't be any missing content strings.
    expect(screen.queryByText(/pages\.claimsReview/i)).not.toBeInTheDocument();
  });

  it("submits the application when the user clicks Submit for a Part 1 review", async () => {
    const { completeSpy, submitSpy } = setup();

    userEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(submitSpy).toHaveBeenCalledWith("mock_application_id");
    });

    expect(completeSpy).not.toHaveBeenCalled();
  });

  it("completes the application when the user clicks Submit for a Part 3 review", async () => {
    const { completeSpy, submitSpy } = setup({
      claim: new MockBenefitsApplicationBuilder().complete().create(),
    });

    userEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(completeSpy).toHaveBeenCalledWith("mock_application_id");
    });

    expect(submitSpy).not.toHaveBeenCalled();
  });

  it("renders a Alert when there are required field errors", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({ type: "required", field: "someField" }),
    ]);

    setup({ appErrors });

    expect(
      screen.getByText(/We’ve added some new questions/i).parentNode
    ).toMatchSnapshot();
  });

  it("does not render a custom Alert when there are required errors not associated to a specific field", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        type: "required",
        field: null,
        rule: "require_employer_notified",
        message:
          "employer_notified must be True if employment_status is Employed",
      }),
    ]);

    setup({ appErrors });

    expect(
      screen.queryByText(/We’ve added some new questions/i)
    ).not.toBeInTheDocument();
  });

  it("renders Alert when there is an error for loading documents", () => {
    const claim = new MockBenefitsApplicationBuilder().complete().create();

    setup({
      appErrors: new AppErrorInfoCollection([
        new AppErrorInfo({
          name: "DocumentsLoadError",
          meta: {
            application_id: claim.application_id,
          },
        }),
      ]),
      claim,
    });

    expect(
      screen.getByText(
        /error was encountered while checking your application for documents/i
      )
    ).toBeInTheDocument();
  });

  it("renders the number of uploaded documents, filtering by document type and leave reason", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .complete()
      .pregnancyLeaveReason()
      .create();

    setup({
      claim,
      documents: [
        new Document({
          application_id: claim.application_id,
          document_type: DocumentType.certification[claim.leave_details.reason],
        }),
        new Document({
          application_id: claim.application_id,
          document_type: DocumentType.certification[claim.leave_details.reason],
        }),
        new Document({
          application_id: claim.application_id,
          document_type: DocumentType.identityVerification,
        }),
      ],
    });

    expect(
      screen.getByRole("heading", { name: /Upload identity document/i })
        .parentNode.nextElementSibling
    ).toMatchSnapshot();
    expect(
      screen.getByRole("heading", { name: /Upload certification document/i })
        .parentNode.nextElementSibling
    ).toMatchSnapshot();
  });

  it("does not render certification document row when claim is for future bonding leave", () => {
    const futureDate = DateTime.local().plus({ months: 1 }).toISODate();

    setup({
      claim: new MockBenefitsApplicationBuilder()
        .complete()
        .bondingBirthLeaveReason(futureDate)
        .hasFutureChild()
        .create(),
    });

    expect(screen.queryByText(/Upload certification/i)).not.toBeInTheDocument();
  });

  it("renders Other Leave section when the application has answers for that section", () => {
    const headingTextMatch = /Other leave, benefits, and income/i;
    const claim = new MockBenefitsApplicationBuilder().complete().create();
    claim.has_other_incomes = false;
    claim.has_employer_benefits = false;

    // Renders when falsy
    setup({ claim });

    expect(
      screen.getByRole("heading", { name: headingTextMatch })
    ).toBeInTheDocument();

    // But doesn't render when null
    cleanup();
    claim.has_other_incomes = null;
    claim.has_employer_benefits = null;
    claim.has_previous_leaves_same_reason = null;
    claim.has_previous_leaves_other_reason = null;
    claim.has_concurrent_leave = null;
    setup({ claim });

    expect(
      screen.queryByRole("heading", { name: headingTextMatch })
    ).not.toBeInTheDocument();
  });

  describe("Work patterns", () => {
    it("displays correct work pattern details when pattern type is Fixed", () => {
      setup({
        claim: new MockBenefitsApplicationBuilder()
          .part1Complete()
          .fixedWorkPattern()
          .create(),
      });

      expect(
        screen.getByText(/Each week I work the same number/i)
      ).toBeInTheDocument();

      expect(
        screen.getByText(/Weekly work hours/i).nextElementSibling
      ).toMatchSnapshot();
    });

    it("displays correct work pattern details when pattern type is Variable", () => {
      setup({
        claim: new MockBenefitsApplicationBuilder()
          .part1Complete()
          .variableWorkPattern()
          .create(),
      });

      expect(
        screen.getByText(/My schedule is not consistent from week to week/i)
      ).toBeInTheDocument();

      expect(
        screen.getByText(/Average weekly hours/i).nextSibling
      ).toHaveTextContent("40h");
    });
  });

  it("does not render ACH content when payment method is Check", () => {
    const textMatch = /Routing number/i;

    setup({
      claim: new MockBenefitsApplicationBuilder().complete().check().create(),
    });

    expect(screen.queryByText(textMatch)).not.toBeInTheDocument();

    cleanup();
    setup({
      claim: new MockBenefitsApplicationBuilder()
        .complete()
        .directDeposit()
        .create(),
    });

    expect(screen.queryByText(textMatch)).toBeInTheDocument();
  });

  it("does not render Employer rows when Claimant is unemployed", () => {
    const einTextMatch = "Employer’s EIN";
    const notifyTextMatch = "Notified employer";
    const claim = new MockBenefitsApplicationBuilder()
      .complete()
      .employed()
      .create();

    setup({ claim });
    expect(screen.queryByText(einTextMatch)).toBeInTheDocument();
    expect(screen.queryByText(notifyTextMatch)).toBeInTheDocument();

    cleanup();
    claim.employment_status = EmploymentStatus.unemployed;
    setup({ claim });

    expect(screen.queryByText(einTextMatch)).not.toBeInTheDocument();
    expect(screen.queryByText(notifyTextMatch)).not.toBeInTheDocument();
  });

  it.each([
    [
      "medical",
      new MockBenefitsApplicationBuilder().part1Complete().medicalLeaveReason(),
    ],
    [
      "family",
      new MockBenefitsApplicationBuilder()
        .part1Complete()
        .bondingBirthLeaveReason(),
    ],
    [
      "caring",
      new MockBenefitsApplicationBuilder().part1Complete().caringLeaveReason(),
    ],
  ])("renders expected review row for %s leave reason", (reason, claim) => {
    const textMatch = {
      medical: "Medical leave for pregnancy or birth",
      family: "Family leave type",
      caring: "Family member's relationship",
    }[reason];

    setup({ claim: claim.create() });

    expect(screen.queryByText(textMatch)).toBeInTheDocument();
  });

  it("renders WeeklyTimeTable for the reduced leave period when work pattern is Fixed", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .part1Complete()
      .fixedWorkPattern()
      .reducedSchedule()
      .create();

    setup({ claim });

    expect(
      screen.queryByText("Hours off per week").parentNode
    ).toMatchSnapshot();
  });

  it("renders total time for the reduced leave period when work pattern is Variable", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .part1Complete()
      .variableWorkPattern()
      .reducedSchedule()
      .create();

    setup({ claim });

    expect(
      screen.queryByText("Hours off per week").parentNode
    ).toMatchSnapshot();
  });

  it("renders the leave frequency and duration in plain language", () => {
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

    intermittentLeavePeriodPermutations.forEach((intermittentLeavePeriod) => {
      const claim = new MockBenefitsApplicationBuilder()
        .part1Complete()
        .create();
      claim.leave_details.intermittent_leave_periods = [
        intermittentLeavePeriod,
      ];

      setup({ claim });

      expect(
        screen.queryByText(/Estimated [0-9]+ absences/i)
      ).toMatchSnapshot();

      cleanup();
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

    it("renders all data fields when all data are present", () => {
      const { container } = render(
        <EmployerBenefitList entries={entries} reviewRowLevel="4" />
      );

      expect(container).toMatchSnapshot();
    });

    it("doesn't render missing data when amount fields are missing", () => {
      const entries = [
        new EmployerBenefit({
          benefit_end_date: "2021-12-30",
          benefit_start_date: "2021-08-12",
          benefit_type: EmployerBenefitType.permanentDisability,
        }),
      ];
      const { container } = render(
        <EmployerBenefitList entries={entries} reviewRowLevel="4" />
      );

      expect(container).toMatchSnapshot();
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

      const { container } = render(
        <PreviousLeaveList
          entries={entries}
          type="otherReason"
          startIndex={1}
          reviewRowLevel="4"
        />
      );

      expect(container).toMatchSnapshot();
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

      const { container } = render(
        <PreviousLeaveList
          entries={entries}
          type="sameReason"
          startIndex={1}
          reviewRowLevel="4"
        />
      );

      expect(container).toMatchSnapshot();
    });
  });

  describe("OtherIncomeList", () => {
    it("renders all data fields when all data are present", () => {
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
      const { container } = render(
        <OtherIncomeList entries={entries} reviewRowLevel="4" />
      );

      expect(container).toMatchSnapshot();
    });

    it("doesn't render missing data when amount fields are missing", () => {
      const entries = [
        new OtherIncome({
          income_end_date: "2021-12-30",
          income_start_date: "2021-08-12",
          income_type: OtherIncomeType.otherEmployer,
        }),
      ];
      const { container } = render(
        <OtherIncomeList entries={entries} reviewRowLevel="4" />
      );

      expect(container).toMatchSnapshot();
    });
  });

  describe("OtherLeaveEntry", () => {
    it("renders all data fields when all data are present", () => {
      const label = "Benefit 1";
      const type = "Medical or family leave";
      const dates = "07-22-2020 - 09-22-2020";
      const amount = "$250 per month";
      const { container } = render(
        <OtherLeaveEntry
          label={label}
          type={type}
          dates={dates}
          amount={amount}
          reviewRowLevel="4"
        />
      );

      expect(container).toMatchSnapshot();
    });

    it("doesn't render missing data when amount is missing", () => {
      const label = "Benefit 1";
      const type = "Medical or family leave";
      const dates = "07-22-2020 - 09-22-2020";
      const { container } = render(
        <OtherLeaveEntry
          label={label}
          type={type}
          dates={dates}
          amount={null}
          reviewRowLevel="4"
        />
      );

      expect(container).toMatchSnapshot();
    });
  });
});
