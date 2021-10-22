import User, { UserLeaveAdministrator } from "../../../../src/models/User";
import CannotVerify from "../../../../src/pages/employers/organizations/cannot-verify";
import { renderPage } from "../../../test-utils";

describe("CannotVerify", () => {
  it("renders the page", () => {
    const { container } = renderPage(
      CannotVerify,
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
        },
      },
      {
        query: { employer_id: "mock_employer_id" },
      }
    );
    expect(container).toMatchSnapshot();
  });
});
