import { UserLeaveAdministrator } from "../../../src/models/User";
import VerifyBusiness from "../../../src/pages/employers/verify-business";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../../test-utils";
import routes from "../../../src/routes";

jest.mock("../../../src/hooks/useAppLogic");

describe("VerifyBusiness", () => {
  const query = { employer_id: "mock_employer_id" };
  mockRouter.pathname = routes.employers.VerifyBusiness;

  const { wrapper } = renderWithAppLogic(VerifyBusiness, {
    diveLevels: 1,
    props: {
      query,
    },
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
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });
});
