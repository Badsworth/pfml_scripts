import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeaveReason from "../../../src/models/LeaveReason";
import LeaveReasonPage from "../../../src/pages/applications/leave-reason";
import { ReasonQualifier } from "../../../src/models/Claim";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeaveReasonPage", () => {
  describe("when type feature flags are enabled", () => {
    let wrapper;

    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowMedicalLeaveType: true,
        claimantShowMilitaryLeaveTypes: true,
      };
      ({ wrapper } = renderWithAppLogic(LeaveReasonPage, {
        claimAttrs: new MockClaimBuilder().create(),
      }));
    });

    it("renders the page with all four reasons", () => {
      const choiceGroup = wrapper.find("InputChoiceGroup").first().dive();

      expect(choiceGroup.exists(`[value="${LeaveReason.medical}"]`)).toBe(true);
      expect(choiceGroup.exists(`[value="${LeaveReason.bonding}"]`)).toBe(true);
      expect(
        choiceGroup.exists(`[value="${LeaveReason.activeDutyFamily}"]`)
      ).toBe(true);
      expect(
        choiceGroup.exists(`[value="${LeaveReason.serviceMemberFamily}"]`)
      ).toBe(true);
    });
  });

  describe("when type feature flags are disabled", () => {
    let wrapper;

    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowMedicalLeaveType: false,
        claimantShowMilitaryLeaveTypes: false,
      };
      ({ wrapper } = renderWithAppLogic(LeaveReasonPage, {
        claimAttrs: new MockClaimBuilder().create(),
      }));
    });

    it("renders the page with only the bonding reason", () => {
      const choiceGroup = wrapper.find("InputChoiceGroup").first().dive();

      expect(choiceGroup.exists(`[value="${LeaveReason.medical}"]`)).toBe(
        false
      );
      expect(choiceGroup.exists(`[value="${LeaveReason.bonding}"]`)).toBe(true);
      expect(
        choiceGroup.exists(`[value="${LeaveReason.activeDutyFamily}"]`)
      ).toBe(false);
      expect(
        choiceGroup.exists(`[value="${LeaveReason.serviceMemberFamily}"]`)
      ).toBe(false);
    });
  });

  it("renders the page for medical leave and does not show reason qualifier followup", () => {
    const { wrapper } = renderWithAppLogic(LeaveReasonPage, {
      claimAttrs: new MockClaimBuilder().medicalLeaveReason().create(),
    });

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    expect(
      wrapper.find({ name: "leave_details.reason_qualifier" }).prop("visible")
    ).toBeFalsy();
  });

  describe("when a user selects bonding as their leave reason", () => {
    let appLogic, changeRadioGroup, claim, wrapper;

    beforeEach(() => {
      ({ appLogic, claim, wrapper } = renderWithAppLogic(LeaveReasonPage, {
        claimAttrs: new MockClaimBuilder().create(),
      }));
      ({ changeRadioGroup } = simulateEvents(wrapper));

      changeRadioGroup("leave_details.reason", LeaveReason.bonding);
    });

    it("shows the bonding type question", () => {
      expect(
        wrapper
          .find({ name: "leave_details.reason_qualifier" })
          .parents("ConditionalContent")
          .prop("visible")
      ).toBeTruthy();
    });

    it("calls claims.update with leave reason and reason qualifier for bonding leave", () => {
      changeRadioGroup(
        "leave_details.reason_qualifier",
        ReasonQualifier.newBorn
      );

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
  });

  it("calls claims.update with with only leave reason for medical leave and set child birth/placement date to null", () => {
    const { appLogic, claim, wrapper } = renderWithAppLogic(LeaveReasonPage, {
      claimAttrs: new MockClaimBuilder().medicalLeaveReason().create(),
    });

    act(() => {
      wrapper.find("QuestionPage").simulate("save");
    });

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        child_birth_date: null,
        child_placement_date: null,
        has_future_child_date: null,
        reason: LeaveReason.medical,
        reason_qualifier: null,
      },
    });
  });
});
