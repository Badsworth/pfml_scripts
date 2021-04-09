import User, { RoleDescription } from "../../src/models/User";
import { renderWithAppLogic, simulateEvents, testHook } from "../test-utils";
import ClaimCollection from "../../src/models/ClaimCollection";
import ConvertToEmployer from "../../src/pages/convert-to-employer";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import useAppLogic from "../../src/hooks/useAppLogic";

// jest.mock("@aws-amplify/auth");
// jest.mock("../../src/services/tracker");
// jest.mock("../../src/hooks/useAppLogic");

describe("ConvertToEmployer", () => {
  function render(customProps = {}, options = { claims: [] }) {
    let appLogic;
    mockRouter.pathname = routes.auth.convert;
    process.env.featureFlags = {
      claimantConvertToEmployer: true,
    };

    testHook(() => {
      appLogic = useAppLogic();
      appLogic.users.user = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true
      });
      appLogic.claims.claims = new ClaimCollection(options.claims);
      appLogic.claims.hasLoadedAll = true;
    });

    const { wrapper } = renderWithAppLogic(ConvertToEmployer, {
      props: { appLogic, ...customProps },
    });

    return { appLogic, wrapper };
  }
  it("renders form", () => {
    const { wrapper } = render();
    expect(wrapper).toMatchSnapshot();
  });
  it("can convert to employer account", async () => {
    const fein = "123456789";
    const { appLogic, wrapper } = render();
    const { changeField, submitForm } = simulateEvents(wrapper);
    changeField("employer_fein", fein);
    await submitForm();
    expect(appLogic.users.updateUser).toHaveBeenCalledWith(
      expect.any(String), {
      role: {
        role_description: RoleDescription.employer,
      },
      user_leave_administrator: {
        employer_fein: fein,
      },
    });
  });
});
