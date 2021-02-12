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
  const WrappedComponent = withWithholding(PageComponent);

  function render(appLogic) {
    act(() => {
      wrapper = mount(
        <WrappedComponent appLogic={appLogic} query={{ employer_id }} />
      );
    });
  }

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    appLogic.users.user = new User({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
      user_leave_administrators: [
        new UserLeaveAdministrator({
          employer_dba: "Test Company",
          employer_fein: "1298391823",
          employer_id: "mock-employer-id",
          verified: true,
        }),
      ],
    });
  });

  it("renders a spinner when withholding is loading", () => {
    render(appLogic);

    expect(wrapper.find("Spinner").exists()).toBe(true);
  });

  it("fetches withholding data", () => {
    render(appLogic);

    expect(appLogic.employers.loadWithholding).toHaveBeenCalledWith(
      "mock-employer-id"
    );
  });
});
