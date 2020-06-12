import React from "react";
import StateId from "../../../src/pages/claims/state-id";
import User from "../../../src/models/User";
import routes from "../../../src/routes";
import { shallow } from "enzyme";
import usersApi from "../../../src/api/usersApi";

jest.mock("../../../src/api/usersApi");
const claim_id = "12345";
const render = (props = {}) => {
  const allProps = {
    user: new User(),
    setUser: jest.fn(),
    query: { claim_id },
    ...props,
  };
  return {
    props: allProps,
    wrapper: shallow(<StateId {...allProps} />),
  };
};

describe("StateId", () => {
  let wrapper;

  beforeEach(() => {
    ({ wrapper } = render());
  });

  it("initially renders the page without an id field", () => {
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
  });

  it("will redirect to the upload other ID page", () => {
    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      `${routes.claims.uploadOtherId}?claim_id=${claim_id}`
    );
  });

  describe("when user has a state id", () => {
    it("renders id field", () => {
      const user = new User({
        has_state_id: true,
        state_id: "12345",
      });
      ({ wrapper } = render({ user }));

      expect(
        wrapper.update().find("ConditionalContent").prop("visible")
      ).toBeTruthy();
    });

    it("will redirect to the upload state ID page", () => {
      const user = new User({
        has_state_id: true,
        state_id: "12345",
      });
      ({ wrapper } = render({ user }));

      expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
        `${routes.claims.uploadStateId}?claim_id=${claim_id}`
      );
    });
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();
      const { props, wrapper: component } = render();

      await component.find("QuestionPage").simulate("save");

      expect(usersApi.updateUser).toHaveBeenCalledTimes(1);
      expect(props.setUser).toHaveBeenCalledWith(expect.any(User));
    });
  });
});
