// TODO (PORTAL-1148) Update to use createMockClaim when ready
import { createMockBenefitsApplication, renderPage } from "../../../test-utils";

import { Payments } from "../../../../src/pages/applications/status/payments";
import { mockRouter } from "next/router";
import routes from "../../../../src/routes";
import { screen } from "@testing-library/react";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status.payments;

const defaultClaimDetail = {
  application_id: "mock-application-id",
  fineos_absence_id: "mock-absence-case-id",
  employer: { employer_fein: "12-1234567" },
};

const props = {
  query: {
    absence_id: defaultClaimDetail.fineos_absence_id,
  },
};

describe("Payments", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      claimantShowPayments: true,
    };
  });

  it("redirects to status page if feature flag is not enabled", () => {
    process.env.featureFlags = {
      claimantShowPayments: false,
    };

    const goToSpy = jest.fn();
    renderPage(
      Payments,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.claims.loadClaimDetail = jest.fn();
          appLogicHook.portalFlow.goTo = goToSpy;
        },
      },
      props
    );

    expect(goToSpy).toHaveBeenCalledWith(routes.applications.status.claim, {
      absence_id: props.query.absence_id,
    });
  });

  it("renders the back button", () => {
    renderPage(Payments, undefined, props);

    const backButton = screen.getByRole("link", {
      name: /back to your applications/i,
    });

    expect(backButton).toBeInTheDocument();
  });

  it("renders the `changes to payments` section", () => {
    renderPage(Payments, undefined, props);

    const section = screen.getByTestId("changes-to-payments");
    expect(section).toMatchSnapshot();
  });

  it("renders the `questions?` section", () => {
    renderPage(Payments, undefined, props);

    const section = screen.getByTestId("questions");
    expect(section).toMatchSnapshot();

    const details = screen.getAllByText(/call the contact center at/i);
    expect(details.length).toBe(2);
  });

  it.each(["continuous", "intermittent", "reducedSchedule"])(
    "renders expected content for %s leave",
    (leavePeriodType) => {
      renderPage(
        Payments,
        {
          addCustomSetup: (appLogicHook) => {
            // TODO (PORTAL-1148) Update to use createMockClaim when ready
            appLogicHook.claims.claimDetail =
              createMockBenefitsApplication(leavePeriodType);
          },
        },
        props
      );

      const section = screen.getByTestId("when-to-expect-payments");
      expect(section).toMatchSnapshot();
    }
  );
});
