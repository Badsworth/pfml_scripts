import Name from "../../../src/pages/claims/name";
import React from "react";
import User from "../../../src/models/User";
import { shallow } from "enzyme";
import usersApi from "../../../src/api/usersApi";

jest.mock("../../../src/api/usersApi");

describe("Name", () => {
  let setUser, user, wrapper;

  beforeEach(() => {
    user = new User();
    setUser = jest.fn();
    wrapper = shallow(<Name user={user} setUser={setUser} />);
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the page prefilled with user information", () => {
    user = new User({
      firstName: "Aquib",
      middleName: "cricketer",
      lastName: "Khan",
    });
    wrapper = shallow(<Name user={user} setUser={setUser} />);
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
