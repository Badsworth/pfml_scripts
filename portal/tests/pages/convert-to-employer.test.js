import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
  testHook,
} from "../test-utils";
import User, {
  RoleDescription,
  UserLeaveAdministrator,
} from "../../src/models/User";

import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import ConvertToEmployer from "../../src/pages/user/convert-to-employer";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("ConvertToEmployer", () => {
  function render(renderProps = {}, options = { user: {}, claims: [] }) {
    let appLogic;
    mockRouter.pathname = routes.auth.convert;
    testHook(() => {
      appLogic = useAppLogic();
      appLogic.users.user = new User({
        user_id: "mock_user_id",
        consented_to_data_sharing: true,
        ...options.user,
      });
      appLogic.users.convertUser = jest.fn((user_id, postData) => null);
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection(options.claims);
      appLogic.benefitsApplications.hasLoadedAll = true;
    });

    const { wrapper } = renderWithAppLogic(ConvertToEmployer, {
      ...renderProps,
      props: { appLogic },
    });

    return { appLogic, wrapper };
  }

  it("renders form when user has no claims", () => {
    const { wrapper } = render();
    expect(wrapper.find("InputText").length).toEqual(1);
    expect(wrapper).toMatchSnapshot();
  });

  it("can convert to employer account when user has no claims", async () => {
    const fein = "123456789";
    const { appLogic, wrapper } = render();
    const { changeField, submitForm } = simulateEvents(wrapper);
    changeField("employer_fein", fein);
    await submitForm();
    expect(appLogic.users.convertUser).toHaveBeenCalledWith("mock_user_id", {
      employer_fein: fein,
    });
  });

  it("does not render page when user has at least one claim", () => {
    const claims = [new MockBenefitsApplicationBuilder().submitted().create()];
    const { appLogic, wrapper } = render({}, { claims });
    expect(wrapper.find("InputText").length).toEqual(0);
    expect(appLogic.portalFlow.goToPageFor).toHaveBeenCalledWith(
      "PREVENT_CONVERSION",
      {},
      {},
      { redirect: true }
    );
  });

  it("redirects to employer organizations when user is an employer", () => {
    const { appLogic } = render(
      {},
      {
        user: {
          roles: [
            {
              role_description: RoleDescription.employer,
            },
          ],
          user_leave_administrators: [
            new UserLeaveAdministrator({
              employer_fein: "12-3456789",
            }),
          ],
        },
      }
    );
    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      routes.employers.organizations,
      {},
      { redirect: true }
    );
  });
});
