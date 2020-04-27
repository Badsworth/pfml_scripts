import React from "react";
import StateId from "../../../src/pages/claims/state-id";
import User from "../../../src/models/User";
import routes from "../../../src/routes";
import { shallow } from "enzyme";
import usersApi from "../../../src/api/usersApi";

jest.mock("../../../src/api/usersApi");

describe("StateId", () => {
  let setUser, user, wrapper;

  beforeEach(() => {
    user = new User();
    setUser = jest.fn();
    wrapper = shallow(<StateId user={user} setUser={setUser} />);
  });

  it("initially renders the page without an id field", () => {
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
  });

  it("will redirect to ssn page", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      routes.claims.ssn
    );
  });

  describe("when user has a state id", () => {
    it("renders id field", () => {
      user = new User({
        hasStateId: true,
        stateId: "12345",
      });
      wrapper = shallow(<StateId user={user} setUser={setUser} />);

      expect(
        wrapper.update().find("ConditionalContent").prop("visible")
      ).toBeTruthy();
    });
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
