import User, { UserLeaveAdministrator } from "../../src/models/User";
import { screen, waitFor } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import EmployerClaim from "../../src/models/EmployerClaim";
import React from "react";
import { renderPage } from "../test-utils";
import withEmployerClaim from "../../src/hoc/withEmployerClaim";

const mockAbsenceId = "NTN-111-ABS-01";
const mockPageContent = "Claim is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setup({ addCustomSetup } = {}) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      Application: {props.claim?.fineos_absence_id}
    </div>
  );
  const WrappedComponent = withEmployerClaim(PageComponent);

  return renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    {
      query: {
        absence_id: mockAbsenceId,
      },
    }
  );
}

describe("withEmployerClaim", () => {
  it("shows spinner when loading claim state", async () => {
    setup();

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });

  it("doesn't show the spinner if there are errors", () => {
    const { container } = setup({
      addCustomSetup: (appLogic) => {
        appLogic.appErrors = new AppErrorInfoCollection([new AppErrorInfo()]);
      },
    });

    expect(container).toBeEmptyDOMElement();
  });

  it("requires user to be logged in", async () => {
    let spy;

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.auth, "requireLogin");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });
  });

  it("renders the page when claim state is loaded", async () => {
    const mockClaim = new EmployerClaim({ fineos_absence_id: mockAbsenceId });

    setup({
      addCustomSetup: (appLogic) => {
        appLogic.employers.claim = mockClaim;
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the claim as a prop to our page component:
    expect(
      await screen.findByText(mockClaim.fineos_absence_id, { exact: false })
    ).toBeInTheDocument();
  });

  it("redirects to Verify Contributions page when claim is associated with an unverified employer that can be verified", () => {
    let spy;
    const mockEmployerId = "dda903f-f093f-ff900";
    const mockUser = new User({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
      user_leave_administrators: [
        new UserLeaveAdministrator({
          employer_id: mockEmployerId,
          // These two fields indicate the employer is "verifiable":
          has_verification_data: true,
          verified: false,
        }),
      ],
    });
    const mockClaim = new EmployerClaim({
      employer_id: mockEmployerId,
      fineos_absence_id: mockAbsenceId,
    });

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
        appLogic.users.user = mockUser;
        appLogic.employers.claim = mockClaim;
        appLogic.portalFlow.pathWithParams = "/test-route";
      },
    });

    expect(spy).toHaveBeenCalledWith(
      "/employers/organizations/verify-contributions",
      {
        employer_id: mockEmployerId,
        next: "/test-route",
      }
    );
  });

  it("redirects to Cannot Verify page when user has employer that cannot be verified", () => {
    let spy;
    const mockEmployerId = "dda903f-f093f-ff900";
    const mockUser = new User({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
      user_leave_administrators: [
        new UserLeaveAdministrator({
          employer_id: mockEmployerId,
          // These two fields indicate the employer is "unverifiable":
          has_verification_data: false,
          verified: false,
        }),
      ],
    });
    const mockClaim = new EmployerClaim({
      employer_id: mockEmployerId,
      fineos_absence_id: mockAbsenceId,
    });

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
        appLogic.users.user = mockUser;
        appLogic.employers.claim = mockClaim;
        appLogic.portalFlow.pathWithParams = "/test-route";
      },
    });

    expect(spy).toHaveBeenCalledWith("/employers/organizations/cannot-verify", {
      employer_id: mockEmployerId,
    });
  });
});
