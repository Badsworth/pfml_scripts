import User, { UserLeaveAdministrator } from "../../src/models/User";
import { act, screen } from "@testing-library/react";
import React from "react";
import Withholding from "../../src/models/Withholding";
import { renderPage } from "../test-utils";
import withWithholding from "../../src/hoc/withWithholding";

const mockEmployerId = "mock-employer-id";
const mockPageContent = "Claim is loaded. This is the page.";

jest.mock("../../src/hooks/useAppLogic");

function setupUser(verified = false) {
  return new User({
    consented_to_data_sharing: true,
    user_leave_administrators: [
      new UserLeaveAdministrator({
        employer_id: mockEmployerId,
        has_verification_data: true,
        verified,
      }),
    ],
  });
}

function setup({ addCustomSetup } = {}) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      filing_period: {props.withholding.filing_period}
    </div>
  );
  const WrappedComponent = withWithholding(PageComponent);

  return renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    {
      query: {
        employer_id: mockEmployerId,
      },
    }
  );
}

describe("withWithholding", () => {
  it("shows spinner when loading withholding state", async () => {
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.users.user = setupUser();
      },
    });

    await act(async () => {
      await expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });
  });

  it("renders the page when witholding state is loaded", async () => {
    const mockWitholding = new Withholding({
      filing_period: "2020-01-01",
    });

    setup({
      addCustomSetup: (appLogic) => {
        appLogic.users.user = setupUser();
        appLogic.employers.loadWithholding = jest
          .fn()
          .mockResolvedValue(mockWitholding);
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the withholding as a prop to our page component:
    expect(
      await screen.findByText(mockWitholding.filing_period, { exact: false })
    ).toBeInTheDocument();
  });

  it("redirects to the Verification Success page if employer is already verified", () => {
    let spy;
    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
        appLogic.users.user = setupUser(true);
      },
    });

    expect(spy).toHaveBeenCalledWith("/employers/organizations/success", {
      employer_id: mockEmployerId,
    });
  });
});
