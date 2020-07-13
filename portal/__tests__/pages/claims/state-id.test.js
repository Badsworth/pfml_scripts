import StateId from "../../../src/pages/claims/state-id";
import { act } from "react-dom/test-utils";
import { mockUpdateUser } from "../../../src/api/UsersApi";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/api/UsersApi");

describe("StateId", () => {
  it("initially renders the page without an id field", () => {
    const { wrapper } = renderWithAppLogic(StateId);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
  });

  describe("when user has a state id", () => {
    it("renders id field", () => {
      const { wrapper } = renderWithAppLogic(StateId, {
        userAttrs: {
          has_state_id: true,
          state_id: "12345",
        },
      });

      expect(
        wrapper.update().find("ConditionalContent").prop("visible")
      ).toBeTruthy();
    });
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();
      const { wrapper } = renderWithAppLogic(StateId);

      await act(async () => {
        await wrapper.find("QuestionPage").simulate("save");
      });

      expect(mockUpdateUser).toHaveBeenCalledTimes(1);
    });
  });
});
