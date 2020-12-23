import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import PreviousLeaves from "../../../src/pages/applications/previous-leaves";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";

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
    const hintWrapper = shallow(wrapper.find("InputChoiceGroup").prop("hint"));

    expect(wrapper).toMatchSnapshot();
    expect(hintWrapper.find("Trans").dive()).toMatchSnapshot();
  });

  describe("when user clicks continue", () => {
    it("calls claims.update", () => {
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });
      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_previous_leaves: claim.has_previous_leaves,
        }
      );
    });
  });
});
