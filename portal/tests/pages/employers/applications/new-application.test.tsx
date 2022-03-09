import { MockEmployerClaimBuilder, renderPage } from "../../../test-utils";
import { render, screen } from "@testing-library/react";
import EmployerClaim from "../../../../src/models/EmployerClaim";
import MockDate from "mockdate";
import NewApplication from "../../../../src/pages/employers/applications/new-application";
import React from "react";
import User from "../../../../src/models/User";
import { merge } from "lodash";
import routes from "../../../../src/routes";
import useAppLogic from "../../../../src/hooks/useAppLogic";
import userEvent from "@testing-library/user-event";

describe("NewApplication", () => {
  const goTo = jest.fn();
  const goToNextPage = jest.fn();
  const goToPageFor = jest.fn();

  const NewApplicationWithAppLogic = (providedProps: {
    claim?: EmployerClaim;
  }) => {
    // default appLogic prop required by components using withUser.
    const defaultAppLogic = useAppLogic();
    defaultAppLogic.auth.requireLogin = jest.fn();
    defaultAppLogic.users.requireUserConsentToDataAgreement = jest.fn();
    defaultAppLogic.users.requireUserRole = jest.fn();
    defaultAppLogic.users.user = new User({ consented_to_data_sharing: true });

    // default props for the purposes of this test.
    const defaultClaim = new MockEmployerClaimBuilder()
      .completed()
      .reviewable("2020-10-10")
      .absenceId("my-absence-id")
      .create();
    const claim = providedProps.claim ?? defaultClaim;
    defaultAppLogic.employers.claim = claim;
    defaultAppLogic.portalFlow.goTo = goTo;
    defaultAppLogic.portalFlow.goToNextPage = goToNextPage;
    defaultAppLogic.portalFlow.goToPageFor = goToPageFor;

    const defaultProps = {
      appLogic: defaultAppLogic,
      claim,
      query: { absence_id: "my-absence-id" },
    };

    const props = merge({}, defaultProps, providedProps);
    return <NewApplication {...props} />;
  };

  beforeEach(() => {
    MockDate.set("2020-10-01");
  });

  it("redirects to status page", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    let goToPageForSpy!: jest.SpyInstance;

    renderPage(
      NewApplication,
      {
        addCustomSetup: (appLogic) => {
          goToPageForSpy = jest.spyOn(appLogic.portalFlow, "goToPageFor");

          // TODO (PORTAL-1560): Remove this claim mocking once the page is no longer using the HOC
          const claim = new MockEmployerClaimBuilder()
            .absenceId("mock-absence-id")
            .create();
          appLogic.employers.claim = claim;
        },
        pathname: routes.employers.newApplication,
      },
      {
        query: {
          absence_id: "mock-absence-id",
        },
      }
    );

    expect(goToPageForSpy).toHaveBeenCalledWith(
      "REDIRECT",
      {},
      { absence_id: "mock-absence-id" },
      { redirect: true }
    );
  });

  it("redirects to the 'Not Reviewable' page if the claim is not reviewable", () => {
    const notReviewableClaim = new MockEmployerClaimBuilder()
      .completed()
      .absenceId("my-absence-id")
      .create();

    render(<NewApplicationWithAppLogic claim={notReviewableClaim} />);

    expect(goToPageFor).toHaveBeenCalledWith(
      "CLAIM_NOT_REVIEWABLE",
      {},
      { absence_id: "my-absence-id" },
      { redirect: true }
    );
  });

  it("initially renders without any option selection", () => {
    const { container } = render(<NewApplicationWithAppLogic />);

    expect(screen.getByRole("radio", { name: /Yes/ })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: /No/ })).not.toBeChecked();
    expect(
      screen.queryByText(/Start the review process/)
    ).not.toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  describe("when 'Yes' is selected", () => {
    it("shows the 'Start the review process' section", () => {
      render(<NewApplicationWithAppLogic />);

      userEvent.click(screen.getByRole("radio", { name: /Yes/ }));

      expect(
        screen.queryByText(/Start the review process/)
      ).toBeInTheDocument();
    });

    it("navigates to the next page upon clicking 'Agree and submit'", () => {
      render(<NewApplicationWithAppLogic />);
      userEvent.click(screen.getByRole("radio", { name: /Yes/ }));

      userEvent.click(screen.getByRole("button", { name: /Agree and submit/ }));

      expect(goToNextPage).toHaveBeenCalledWith(
        {},
        { absence_id: "my-absence-id" }
      );
    });
  });

  describe("when 'No' is selected", () => {
    it("navigates to the confirmation page upon clicking 'Submit'", () => {
      render(<NewApplicationWithAppLogic />);
      userEvent.click(screen.getByRole("radio", { name: /No/ }));

      userEvent.click(screen.getByRole("button", { name: /Submit/ }));

      expect(goToPageFor).toHaveBeenCalledWith(
        "CONFIRMATION",
        {},
        { absence_id: "my-absence-id" }
      );
    });
  });
});
