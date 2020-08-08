import ConsentToDataSharing from "../../../src/pages/user/consent-to-data-sharing";
import React from "react";
import User from "../../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { mockUpdateUser } from "../../../src/api/UsersApi";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/api/UsersApi");

describe("ConsentToDataSharing", () => {
  let appLogic, wrapper;
  const user_id = "mock-user-id";

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    appLogic.users.user = new User({ user_id });

    wrapper = shallow(<ConsentToDataSharing appLogic={appLogic} />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the user agrees and submits the form", () => {
    beforeEach(async () => {
      await act(async () => {
        await wrapper
          .find("form")
          .simulate("submit", { preventDefault: jest.fn() });
      });
    });

    it("sets user's consented_to_data_sharing field to true", () => {
      expect(mockUpdateUser).toHaveBeenCalledWith(user_id, {
        consented_to_data_sharing: true,
      });
    });

    it("routes to homepage", () => {
      expect(mockRouter.push).toHaveBeenCalledWith("/");
    });
  });
});
