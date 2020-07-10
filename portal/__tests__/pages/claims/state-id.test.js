import React from "react";
import StateId from "../../../src/pages/claims/state-id";
import User from "../../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockUpdateUser } from "../../../src/api/UsersApi";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/api/UsersApi");

const claim_id = "12345";
const render = (props = {}) => {
  let appLogic;

  testHook(() => {
    appLogic = useAppLogic();
  });

  appLogic.user = props.user || new User();

  const allProps = {
    appLogic,
    query: { claim_id },
    claim: {},
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
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();
      const { wrapper: component } = render();
      await act(async () => {
        await component.find("QuestionPage").simulate("save");
      });

      expect(mockUpdateUser).toHaveBeenCalledTimes(1);
    });
  });
});
