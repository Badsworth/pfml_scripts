import DateOfBirth from "../../../src/pages/claims/date-of-birth";
import React from "react";
import User from "../../../src/models/User";
import { shallow } from "enzyme";

describe("DateOfBirth", () => {
  let setUser, user, wrapper;

  beforeEach(() => {
    user = new User();
    setUser = jest.fn();
    wrapper = shallow(<DateOfBirth user={user} setUser={setUser} />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("sets user state after successful save", async () => {
    await wrapper.find("QuestionPage").simulate("save");
    expect(setUser).toHaveBeenCalled();
  });
});
