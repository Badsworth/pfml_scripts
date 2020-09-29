import { LeaveReason, ReasonQualifier } from "../../../src/models/Claim";
import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeaveReasonPage from "../../../src/pages/claims/leave-reason";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeaveReasonPage", () => {
  let appLogic, changeRadioGroup, claim, wrapper;
  function render() {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(LeaveReasonPage, {
      claimAttrs: claim,
    }));
    ({ changeRadioGroup } = simulateEvents(wrapper));
  }

  it("renders the page for medical leave and does not show reason qualifier followup", () => {
    claim = new MockClaimBuilder().medicalLeaveReason().create();
    render();
    expect(wrapper).toMatchSnapshot();
    expect(
      wrapper.find({ name: "leave_details.reason_qualifier" }).prop("visible")
    ).toBeFalsy();
  });

  describe("when a user selects bonding as their leave reason", () => {
    beforeEach(() => {
      changeRadioGroup("leave_details.reason", LeaveReason.bonding);
    });

    it("shows the bonding type question", () => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
      render();
      expect(
        wrapper
          .find({ name: "leave_details.reason_qualifier" })
          .parents("ConditionalContent")
          .prop("visible")
      ).toBeTruthy();
    });

    describe("when user clicks continue", () => {
      it("calls claims.update with leave reason and reason qualifier for bonding leave", () => {
        claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
        render();
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            leave_details: {
              reason: LeaveReason.bonding,
              reason_qualifier: ReasonQualifier.newBorn,
            },
          }
        );
      });

      it("calls claims.update with with only leave reason for medical leave", () => {
        claim = new MockClaimBuilder().medicalLeaveReason().create();
        render();
        act(() => {
          wrapper.find("QuestionPage").simulate("save");
        });
        expect(appLogic.claims.update).toHaveBeenCalledWith(
          claim.application_id,
          {
            leave_details: {
              reason: LeaveReason.medical,
              reason_qualifier: null,
            },
          }
        );
      });
    });
  });
});
