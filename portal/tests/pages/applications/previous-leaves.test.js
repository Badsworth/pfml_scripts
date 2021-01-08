import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import PreviousLeaves from "../../../src/pages/applications/previous-leaves";
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
    it("calls claims.update", async () => {
      const { submitForm } = simulateEvents(wrapper);

      await submitForm();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_previous_leaves: claim.has_previous_leaves,
        }
      );
    });

    it("sends previous_leaves as null to the API if has_previous_leaves changes to no", async () => {
      claim = new MockClaimBuilder()
        .previousLeavePregnancyFromOtherEmployer()
        .create();

      ({ appLogic, wrapper } = renderWithAppLogic(PreviousLeaves, {
        claimAttrs: claim,
      }));

      const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

      changeRadioGroup("has_previous_leaves", "false");

      await submitForm();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          has_previous_leaves: false,
          previous_leaves: null,
        }
      );
    });
  });
});
