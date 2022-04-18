import ChangeRequest, { ChangeRequestType } from "src/models/ChangeRequest";
import { AbsencePeriod } from "src/models/AbsencePeriod";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import ClaimDetail from "src/models/ClaimDetail";
import LeaveReason from "src/models/LeaveReason";
import Review from "src/pages/applications/modify/review";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";

jest.mock("../../../../src/hooks/useAppLogic");

const change_request_id = "7180eae0-0ad8-46a9-b140-5076863330d2";
const absence_id = "fineos-absence-id";

const setup = (
  changeRequestAttrs: Partial<ChangeRequest> = {},
  absencePeriodAttrs: Partial<AbsencePeriod> = {}
) => {
  return renderPage(
    Review,
    {
      addCustomSetup: (appLogicHook) => {
        appLogicHook.changeRequests.changeRequests = new ApiResourceCollection(
          "change_request_id",
          [
            new ChangeRequest({
              change_request_id,
              fineos_absence_id: absence_id,
              change_request_type: ChangeRequestType.modification,
              documents_submitted_at: "2022-01-01",
              start_date: "2022-01-01",
              end_date: "2022-05-01",
              ...changeRequestAttrs,
            }),
          ]
        );
      },
    },
    {
      query: { change_request_id, absence_id },
      claim_detail: new ClaimDetail({
        fineos_absence_id: absence_id,
        absence_periods: [
          {
            absence_period_start_date: "2022-01-01",
            absence_period_end_date: "2022-03-31",
            fineos_leave_request_id: "fineos-id",
            reason: LeaveReason.pregnancy,
            reason_qualifier_one: "",
            reason_qualifier_two: "",
            period_type: "Continuous",
            request_decision: "Approved",
            ...absencePeriodAttrs,
          },
        ],
      }),
    }
  );
};

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({
    claimantShowModifications: true,
  });
});

describe("Claim Modification Review", () => {
  it("renders page content", () => {
    const { container } = setup();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("it shows cancellation review when claim is approved and change request is withdrawal", () => {
    const { container } = setup(
      { change_request_type: ChangeRequestType.withdrawal },
      { request_decision: "Approved" }
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("it shows withdrawal review when claim is pending and change request is withdrawal", () => {
    const { container } = setup(
      { change_request_type: ChangeRequestType.withdrawal },
      { request_decision: "Pending" }
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("it shows medical to bonding review with proof of birth text when change request is medical to bonding and a document was submitted", () => {
    const { container } = setup({
      change_request_type: ChangeRequestType.medicalToBonding,
      documents_submitted_at: "2022-01-01",
    });
    expect(container.firstChild).toMatchSnapshot();
    expect(
      screen.queryByText(
        /Please upload proof of birth within 90 days of submitting this request/
      )
    ).not.toBeInTheDocument();
  });

  it("it shows medical to bonding review without proof of birth text when change request is medical to bonding and a document was not submitted", () => {
    const { container } = setup({
      change_request_type: ChangeRequestType.medicalToBonding,
      documents_submitted_at: null,
    });
    expect(container.firstChild).toMatchSnapshot();
    expect(
      screen.getByText(
        /Please upload proof of birth within 90 days of submitting this request/
      )
    ).toBeInTheDocument();
  });

  it("it shows extension review when change request is modification and end date is after claim start date", () => {
    const { container } = setup(
      {
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-05-01",
      },
      { absence_period_end_date: "2022-04-01" }
    );
    expect(container.firstChild).toMatchSnapshot();
    expect(
      screen.getByText(
        /They will also get a copy of the certification documents./
      )
    ).toBeInTheDocument();
  });

  it("it shows ending leave early review when change request is modification and end date is before claim start date", () => {
    const { container } = setup(
      {
        change_request_type: ChangeRequestType.modification,
        end_date: "2022-04-01",
      },
      { absence_period_end_date: "2022-05-01" }
    );
    expect(container.firstChild).toMatchSnapshot();
    expect(
      screen.queryByText(
        /They will also get a copy of the certification documents./
      )
    ).not.toBeInTheDocument();
  });

  it("renders PageNotFound if the claimantShowModifications feature flag is not set", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowModification: false,
    });
    setup();

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
