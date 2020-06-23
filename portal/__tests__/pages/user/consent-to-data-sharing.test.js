import ConsentToDataSharing from "../../../src/pages/user/consent-to-data-sharing";
import React from "react";
import User from "../../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { shallow } from "enzyme";
import usersApi from "../../../src/api/usersApi";

jest.mock("../../../src/api/usersApi");

describe("ConsentToDataSharing", () => {
  let setUser, user, wrapper;

  beforeEach(() => {
    user = new User();
    setUser = jest.fn();
    wrapper = shallow(<ConsentToDataSharing user={user} setUser={setUser} />);
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
      expect(usersApi.updateUser).toHaveBeenCalledWith(
        expect.objectContaining({ consented_to_data_sharing: true })
      );
      expect(setUser).toHaveBeenCalledWith(expect.any(User));
    });

    it("routes to homepage", () => {
      expect(mockRouter.push).toHaveBeenCalledWith("/");
    });
  });
});
