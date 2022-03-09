import User, {
  RoleDescription,
  UserLeaveAdministrator,
} from "../../../src/models/User";
import { screen, waitFor } from "@testing-library/react";
import { AppLogic } from "../../../src/hooks/useAppLogic";
import ConvertToEmployee from "../../../src/pages/user/convert-to-employee";
import { renderPage } from "../../test-utils";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const getOptions = (cb?: (appLogic: AppLogic) => void) => {
  return {
    pathname: routes.user.convertToEmployee,
    addCustomSetup: (appLogic: AppLogic) => {
      appLogic.users.convertUserToEmployee = jest.fn();
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
            verified: false,
            has_fineos_registration: false,
            has_verification_data: false,
          }),
        ],
      });
      appLogic.benefitsApplications.isLoadingClaims = false;
      appLogic.benefitsApplications.loadPage = jest.fn();
      if (cb) {
        cb(appLogic);
      }
    },
  };
};

describe("ConvertToEmployee", () => {
  const props = {};
  let options = getOptions();

  it("renders page when user is an employer", () => {
    const { container } = renderPage(ConvertToEmployee, options, props);
    expect(container).toMatchSnapshot();
    expect(screen.getByText(/Convert to employee account/)).toBeInTheDocument();
  });

  it("can convert to employee account when user is an unverified employer", async () => {
    const convertUserToEmployee = jest.fn();
    options = getOptions((appLogic) => {
      appLogic.users.convertUserToEmployee = convertUserToEmployee;
    });
    renderPage(ConvertToEmployee, options, props);
    await waitFor(() => {
      userEvent.click(screen.getByRole("button", { name: "Convert account" }));
    });
    expect(convertUserToEmployee).toHaveBeenCalledWith("mock_user_id");
  });

  it("does not render page when user is not an employer", () => {
    const goTo = jest.fn();
    options = getOptions((appLogic) => {
      appLogic.portalFlow.goTo = goTo;
      appLogic.users.user = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true,
        roles: [],
        user_leave_administrators: [],
      });
    });
    renderPage(ConvertToEmployee, options, props);
    expect(goTo).toHaveBeenCalledWith(
      routes.applications.getReady,
      {},
      { redirect: true }
    );
  });

  it("does not render page when user has any verified employer", () => {
    const goToPageFor = jest.fn();
    options = getOptions((appLogic) => {
      appLogic.portalFlow.goToPageFor = goToPageFor;
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
            verified: true,
            has_fineos_registration: true,
            has_verification_data: true,
          }),
        ],
      });
    });
    renderPage(ConvertToEmployee, options, props);
    expect(goToPageFor).toHaveBeenCalledWith(
      "PREVENT_CONVERSION",
      {},
      {},
      { redirect: true }
    );
  });
});
