import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import GetReady from "../../../src/pages/applications/get-ready";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { screen } from "@testing-library/react";

const setup = (claims = []) => {
  mockRouter.pathname = routes.applications.getReady;

  return renderPage(GetReady, {
    addCustomSetup: (appLogic) => {
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection(claims);
      appLogic.benefitsApplications.hasLoadedAll = true;
    },
  });
};

describe("GetReady", () => {
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
});
