import { MockBenefitsApplicationBuilder, renderPage } from "tests/test-utils";
import { AppLogic } from "src/hooks/useAppLogic";
import BenefitsApplication from "src/models/BenefitsApplication";
import LeaveSpansBenefitYearsInterstitial from "src/features/benefits-application/LeaveSpansBenefitYearsInterstitial";
import applicationSplitBuilder from "lib/mock-helpers/createMockApplicationSplit";
import routes from "src/routes";
import { screen } from "@testing-library/react";

// set up a claim that is split across benefit years
const applicationSplit = applicationSplitBuilder(
  0,
  "both applications submittable"
);
const claimBothSubmittable = new MockBenefitsApplicationBuilder().create();
claimBothSubmittable.computed_application_split =
  applicationSplit.computed_application_split;
claimBothSubmittable.computed_earliest_submission_date =
  applicationSplit.computed_earliest_submission_date;

function setup(
  leaveType: "continuous" | "intermittent" | "reduced",
  claim: BenefitsApplication
) {
  const view = renderPage(
    LeaveSpansBenefitYearsInterstitial,
    {
      pathname: `/applications/leave-spans-benefit-years/${leaveType}`,
      addCustomSetup: (appLogic: AppLogic) => {
        appLogic.portalFlow.pageRoute = `/applications/leave-spans-benefit-years/${leaveType}`;
      },
    },
    {
      query: {
        claim_id: "mock-claim-id",
      },
      claim,
    }
  );

  return { ...view };
}

describe("LeaveSpansBenefitYearsInterstitial", () => {
  it("renders the page", () => {
    setup("continuous", claimBothSubmittable);
    expect(
      screen.queryByText(/we'll automatically split this application into two/)
    ).toBeInTheDocument();
  });

  it("links to the reduced schedule page if the leave type is continuous", () => {
    setup("continuous", claimBothSubmittable);
    const link = screen.getByRole("link", { name: "I understand" });
    expect(link).toHaveAttribute(
      "href",
      routes.applications.leavePeriodReducedSchedule +
        "?claim_id=mock_application_id"
    );
  });

  it("links to the intermittent leave page if the leave type is reduced", () => {
    setup("reduced", claimBothSubmittable);
    const link = screen.getByRole("link", { name: "I understand" });
    expect(link).toHaveAttribute(
      "href",
      routes.applications.leavePeriodIntermittent +
        "?claim_id=mock_application_id"
    );
  });

  it("links to the checklist page if the leave type is intermittent", () => {
    setup("intermittent", claimBothSubmittable);
    const link = screen.getByRole("link", { name: "I understand" });
    expect(link).toHaveAttribute(
      "href",
      routes.applications.checklist + "?claim_id=mock_application_id"
    );
  });
});
