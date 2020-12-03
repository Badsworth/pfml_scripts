import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import PreviousLeaves from "../../../src/pages/applications/previous-leaves";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("PreviousLeaves", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    claim = new MockClaimBuilder().continuous().create();

    ({ appLogic, wrapper } = renderWithAppLogic(PreviousLeaves, {
      claimAttrs: claim,
    }));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user clicks continue", () => {
    it("calls claims.update", () => {
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });
      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          temp: { has_previous_leaves: claim.temp.has_previous_leaves },
        }
      );
    });
  });
});
