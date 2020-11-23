import StateId from "../../../src/pages/applications/state-id";
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
    it("calls claims.update and transforms state ID to uppercase", () => {
      const { appLogic, wrapper } = renderWithAppLogic(StateId, {
        claimAttrs: {
          has_state_id: true,
          mass_id: "sa3456789",
        },
      });

      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        has_state_id: true,
        mass_id: "SA3456789",
      });
    });

    it("calls claims.update successfully when has_state_id is false", () => {
      const { appLogic, wrapper } = renderWithAppLogic(StateId, {
        claimAttrs: {
          has_state_id: false,
          mass_id: null,
        },
      });

      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        has_state_id: false,
        mass_id: null,
      });
    });
  });
});
