import PreviousLeaves from "../../../src/pages/claims/previous-leaves";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("PreviousLeaves", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(PreviousLeaves));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user clicks continue", () => {
    it("calls updateClaim", () => {
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });
      expect(appLogic.updateClaim).toHaveBeenCalledWith(claim.application_id, {
        has_previous_leaves: claim.has_previous_leaves,
      });
    });
  });
});
