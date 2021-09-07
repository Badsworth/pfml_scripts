import { CannotVerify } from "../../../../src/pages/employers/organizations/cannot-verify";
import { UserLeaveAdministrator } from "../../../../src/models/User";
import { renderWithAppLogic } from "../../../test-utils";

jest.mock("../../../../src/hooks/useAppLogic");

describe("cannot verify", () => {
  let wrapper;

  const query = {
    employer_id: "mock_employer_id",
  };

  beforeEach(() => {
    ({ wrapper } = renderWithAppLogic(CannotVerify, {
      diveLevels: 0,
      props: { query },
      userAttrs: {
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Company Name",
            employer_fein: "11-111111",
            employer_id: "mock_employer_id",
            verified: false,
          }),
        ],
      },
    }));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });
});
