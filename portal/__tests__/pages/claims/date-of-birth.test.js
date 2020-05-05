import DateOfBirth from "../../../src/pages/claims/date-of-birth";
import React from "react";
import User from "../../../src/models/User";
import { shallow } from "enzyme";
import usersApi from "../../../src/api/usersApi";

jest.mock("../../../src/api/usersApi");

describe("DateOfBirth", () => {
  let setUser, user, wrapper;
  const claim_id = "12345";

  beforeEach(() => {
    user = new User();
    setUser = jest.fn();
    wrapper = shallow(
      <DateOfBirth user={user} setUser={setUser} query={{ claim_id }} />
    );
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();

      await wrapper.find("QuestionPage").simulate("save");

      expect(usersApi.updateUser).toHaveBeenCalledTimes(1);
      expect(setUser).toHaveBeenCalledWith(expect.any(User));
    });
  });
});
