import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import GetReady from "../../../src/pages/applications/get-ready";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { screen } from "@testing-library/react";

const setup = (claims = [], queryParams) => {
  mockRouter.pathname = routes.applications.getReady;

  return renderPage(
    GetReady,
    {
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection(claims);
        appLogic.benefitsApplications.loadPage = jest.fn();
      },
    },
    { query: queryParams }
  );
};

describe("GetReady", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date(2022, 1, 1));
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  it("renders get ready content", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("doesn't show link to applications when claims do not exist", () => {
    setup();
    expect(
      screen.queryByRole("link", { name: "View all applications" })
    ).not.toBeInTheDocument();
  });

  it("shows link to applications when claims exist", () => {
    const claims = [new MockBenefitsApplicationBuilder().create()];
    setup(claims);
    expect(
      screen.getByRole("link", { name: "View all applications" })
    ).toBeInTheDocument();
  });

  it("displays different copy when tax withholding is enabled", () => {
    process.env.featureFlags = {
      claimantShowTaxWithholding: true,
    };
    const { container } = setup();
    expect(container).toMatchSnapshot();
    expect(
      screen.getByRole("link", { name: "tax professional" })
    ).toBeInTheDocument();
  });

  it("displays success alert when user sets up SMS MFA", () => {
    setup([], { smsMfaConfirmed: "true" });
    expect(screen.getAllByRole("region")[0]).toMatchSnapshot();
  });
});