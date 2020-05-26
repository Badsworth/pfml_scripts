import Confirm from "../../../src/pages/claims/confirm";
import React from "react";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { shallow } from "enzyme";

describe("Confirm", () => {
  it("renders the page", () => {
    const wrapper = shallow(<Confirm />);
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to home", async () => {
    const wrapper = shallow(<Confirm />);
    const event = { preventDefault: jest.fn() };

    await wrapper.find("form").simulate("submit", event);

    expect(mockRouter.push).toHaveBeenCalledWith(routes.home);
  });
});
