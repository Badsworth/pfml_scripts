import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import User, {
  RoleDescription,
  UserLeaveAdministrator,
} from "../../../src/models/User";
import { screen, waitFor } from "@testing-library/react";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../src/hooks/useAppLogic";
import BenefitsApplication from "src/models/BenefitsApplication";
import ConvertToEmployer from "../../../src/pages/user/convert-to-employer";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const getOptions = (cb?: (appLogic: AppLogic) => void) => {
  return {
    pathname: routes.user.convertToEmployer,
    addCustomSetup: (appLogic: AppLogic) => {
      appLogic.users.convertUserToEmployer = jest.fn();
      appLogic.users.user = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true,
      });
      appLogic.benefitsApplications.benefitsApplications =
        new ApiResourceCollection<BenefitsApplication>("application_id", []);
      appLogic.benefitsApplications.isLoadingClaims = false;
      appLogic.benefitsApplications.loadPage = jest.fn();
      if (cb) {
        cb(appLogic);
      }
    },
  };
};

describe("ConvertToEmployer", () => {
  const props = {};
  let options = getOptions();

  it("renders form when user has no claims", () => {
    const { container } = renderPage(ConvertToEmployer, options, props);
    expect(container).toMatchSnapshot();
    expect(screen.getByText(/Convert to employer account/)).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("can convert to employer account when user has no claims", async () => {
    const fein = "123456789";
    const convertUserToEmployer = jest.fn();
    options = getOptions((appLogic) => {
      appLogic.users.convertUserToEmployer = convertUserToEmployer;
    });
    renderPage(ConvertToEmployer, options, props);
    userEvent.type(screen.getByRole("textbox"), fein);
    await waitFor(() => {
      userEvent.click(screen.getByRole("button", { name: "Convert account" }));
    });

    expect(convertUserToEmployer).toHaveBeenCalledWith("mock_user_id", {
      employer_fein: fein,
    });
  });

  it("does not render page when user has at least one claim", () => {
    const goToPageFor = jest.fn();
    const claims = [new MockBenefitsApplicationBuilder().submitted().create()];
    options = getOptions((appLogic) => {
      appLogic.benefitsApplications.benefitsApplications =
        new ApiResourceCollection<BenefitsApplication>(
          "application_id",
          claims
        );
      appLogic.portalFlow.goToPageFor = goToPageFor;
    });
    renderPage(ConvertToEmployer, options, props);
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(goToPageFor).toHaveBeenCalledWith(
      "PREVENT_CONVERSION",
      {},
      {},
      { redirect: true }
    );
  });

  it("redirects to employer organizations when user is an employer", () => {
    const goTo = jest.fn();
    options = getOptions((appLogic) => {
      appLogic.users.user = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true,
        roles: [
          {
            role_id: 1,
            role_description: RoleDescription.employer,
          },
        ],
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_fein: "12-3456789",
          }),
        ],
      });
      appLogic.portalFlow.goTo = goTo;
    });
    renderPage(ConvertToEmployer, options, props);

    expect(goTo).toHaveBeenCalledWith(
      routes.employers.organizations,
      {},
      { redirect: true }
    );
  });
});
