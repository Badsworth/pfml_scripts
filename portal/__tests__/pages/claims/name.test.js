import Name from "../../../src/pages/claims/name";
import React from "react";
import User from "../../../src/models/User";
import { shallow } from "enzyme";

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

  it("sets user state after successful save", async () => {
    await wrapper.find("QuestionPage").simulate("save");
    expect(setUser).toHaveBeenCalled();
  });
});
