import User, { UserLeaveAdministrator } from "../../src/models/User";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";
import withWithholding from "../../src/hoc/withWithholding";

jest.mock("../../src/hooks/useAppLogic");

describe("withWithholding", () => {
  let appLogic, wrapper;
  const employer_id = "mock-employer-id";

  const PageComponent = () => <div />;

  const getUser = (isVerified = false) => {
    return new User({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
      user_leave_administrators: [
        new UserLeaveAdministrator({
          employer_dba: "Test Company",
          employer_fein: "1298391823",
          employer_id: "mock-employer-id",
          verified: isVerified,
        }),
      ],
    });
  };

  async function render({ appLogic, customQuery }) {
    const query = customQuery || { employer_id };
    await act(async () => {
      const WrappedComponent = withWithholding(PageComponent);
      wrapper = await mount(
        <WrappedComponent appLogic={appLogic} query={query} />
      );
    });
  }

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    appLogic.users.user = getUser();
  });

  it("renders a spinner when withholding is loading", async () => {
    await render({ appLogic });

    expect(wrapper.find("Spinner").exists()).toBe(true);
  });

  it("fetches withholding data", async () => {
    await render({ appLogic });

    expect(appLogic.employers.loadWithholding).toHaveBeenCalledWith(
      "mock-employer-id"
    );
  });

  it("redirects to the Verification Success page if employer is already verified", async () => {
    appLogic.users.user = getUser(true);

    await render({ appLogic });

    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      "/employers/organizations/success",
      {
        employer_id: "mock-employer-id",
      }
    );
  });
});
