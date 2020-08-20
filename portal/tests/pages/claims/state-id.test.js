import StateId from "../../../src/pages/claims/state-id";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("StateId", () => {
  it("initially renders the page without an id field", () => {
    const { wrapper } = renderWithAppLogic(StateId);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("ConditionalContent").prop("visible")).toBeFalsy();
  });

  describe("when user has a state id", () => {
    it("renders id field", () => {
      const { wrapper } = renderWithAppLogic(StateId, {
        claimAttrs: {
          has_state_id: true,
        },
      });

      expect(
        wrapper.update().find("ConditionalContent").prop("visible")
      ).toBeTruthy();
    });
  });

  describe("when the form is successfully submitted", () => {
    it("calls claims.update", () => {
      const { appLogic, wrapper } = renderWithAppLogic(StateId, {
        claimAttrs: {
          has_state_id: true,
          mass_id: "123456789",
        },
      });

      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        has_state_id: true,
        mass_id: "123456789",
      });
    });
  });
});
