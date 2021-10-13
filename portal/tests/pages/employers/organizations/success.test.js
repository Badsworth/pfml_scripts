import User, { UserLeaveAdministrator } from "../../../../src/models/User";
import Success from "../../../../src/pages/employers/organizations/success";
import { renderPage } from "../../../test-utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const setup = (props = {}) => {
  let goToSpy;
  const utils = renderPage(
    Success,
    {
      addCustomSetup: (appLogic) => {
        appLogic.users.user = new User({
          consented_to_data_sharing: true,
          user_leave_administrators: [
            new UserLeaveAdministrator({
              employer_dba: "Company Name",
              employer_fein: "12-3456789",
              employer_id: "mock_employer_id",
              verified: false,
            }),
          ],
        });
        goToSpy = jest.spyOn(appLogic.portalFlow, "goTo");
      },
    },
    {
      query: { employer_id: "mock_employer_id", next: "" },
      ...props,
    }
  );
  return { goToSpy, ...utils };
};
describe("Success", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("navigates to Organizations page when clicking 'Continue' button", () => {
    const { goToSpy } = setup();
    userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(goToSpy).toHaveBeenCalledWith("/employers/organizations");
  });

  it("navigates to Organizations page by default if query param is invalid", () => {
    const queryWithoutNextParam = {
      employer_id: "mock_employer_id",
      next: "",
    };
    const { goToSpy } = setup({
      query: queryWithoutNextParam,
    });
    userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(goToSpy).toHaveBeenCalledWith("/employers/organizations");
  });

  it("navigates to New Application page based on next param", () => {
    const queryWithNextParam = {
      employer_id: "mock_employer_id",
      next: "/employers/applications/new-application/?absence_id=mock_absence_id",
    };

    const { goToSpy } = setup({
      query: queryWithNextParam,
    });
    userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(goToSpy).toHaveBeenCalledWith(
      "/employers/applications/new-application/?absence_id=mock_absence_id"
    );
  });
});
