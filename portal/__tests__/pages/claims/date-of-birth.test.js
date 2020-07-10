import DateOfBirth from "../../../src/pages/claims/date-of-birth";
import React from "react";
import User from "../../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockUpdateUser } from "../../../src/api/UsersApi";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/api/UsersApi");

describe("DateOfBirth", () => {
  let wrapper;
  const claim_id = "12345";

  beforeEach(() => {
    let appLogic;

    testHook(() => {
      appLogic = useAppLogic();
    });

    appLogic.user = new User();

    wrapper = shallow(
      <DateOfBirth appLogic={appLogic} query={{ claim_id }} claim={{}} />
    );
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();
      await act(async () => {
        await wrapper.find("QuestionPage").simulate("save");
      });
      expect(mockUpdateUser).toHaveBeenCalledTimes(1);
    });
  });
});
