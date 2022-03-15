import GetReady, {
  GetReadyProps,
} from "../../../src/pages/applications/get-ready";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import routes from "../../../src/routes";
import { screen } from "@testing-library/react";

const setup = (
  claims: BenefitsApplication[] = [],
  queryParams?: GetReadyProps["query"]
) => {
  return renderPage(
    GetReady,
    {
      pathname: routes.applications.getReady,
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.benefitsApplications =
          new ApiResourceCollection<BenefitsApplication>(
            "application_id",
            claims
          );
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

  it("displays success alert when user sets up SMS MFA", () => {
    setup([], { smsMfaConfirmed: "true" });
    expect(screen.getAllByRole("region")[0]).toMatchSnapshot();
  });
});
