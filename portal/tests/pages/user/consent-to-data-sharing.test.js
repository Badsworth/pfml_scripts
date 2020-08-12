import { simulateEvents, testHook } from "../../test-utils";
import ConsentToDataSharing from "../../../src/pages/user/consent-to-data-sharing";
import React from "react";
import User from "../../../src/models/User";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("ConsentToDataSharing", () => {
  let appLogic, wrapper;
  const user_id = "mock-user-id";

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    mockRouter.pathname = routes.user.consentToDataSharing;
    appLogic.users.user = new User({ user_id });

    // Dive once since ConsentToDataSharing is wrapped by withUser
    wrapper = shallow(<ConsentToDataSharing appLogic={appLogic} />).dive();
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the user agrees and submits the form", () => {
    beforeEach(async () => {
      const { submitForm } = simulateEvents(wrapper);
      submitForm();
    });

    it("sets user's consented_to_data_sharing field to true", () => {
      expect(appLogic.users.updateUser).toHaveBeenCalledWith(user_id, {
        consented_to_data_sharing: true,
      });
    });
  });
});
