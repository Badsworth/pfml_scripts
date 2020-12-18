import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import DateOfChild from "../../../src/pages/applications/date-of-child";
import { DateTime } from "luxon";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("DateOfChild", () => {
  let appLogic, claim, wrapper;

  function render() {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(DateOfChild, {
      claimAttrs: claim,
    }));
  }

  it("renders the page", () => {
    render();
    expect(wrapper).toMatchSnapshot();
  });

  const child_birth_date = "leave_details.child_birth_date";
  const child_placement_date = "leave_details.child_placement_date";

  describe("when the claim is for a newborn", () => {
    beforeEach(() => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
    });

    it("shows the birth date input without hint text", () => {
      render();
      expect(wrapper.find({ name: child_birth_date }).exists()).toBeTruthy();
      expect(wrapper.find({ name: child_placement_date }).exists()).toBeFalsy();
      expect(wrapper.find("InputDate").prop("hint")).toBeFalsy();
    });

    it("show the birth hint when claimantShowJan1ApplicationInstructions is true", () => {
      process.env.featureFlags = {
        claimantShowJan1ApplicationInstructions: true,
      };

      render();
      expect(wrapper.find("InputDate").prop("hint")).toMatchInlineSnapshot(
        `"If your child has not been born yet, enter the expected due date."`
      );
    });
  });

  describe("when the claim is for an adoption", () => {
    it("shows the correct input question", () => {
      claim = new MockClaimBuilder().bondingAdoptionLeaveReason().create();
      render();
      expect(
        wrapper.find({ name: child_placement_date }).exists()
      ).toBeTruthy();
      expect(wrapper.find({ name: child_birth_date }).exists()).toBeFalsy();
    });
  });

  describe("when child birth date is in the future", () => {
    const past = "2020-09-30";
    const now = "2020-10-01";
    const future = "2020-10-02";
    let spy;

    beforeAll(() => {
      spy = jest.spyOn(DateTime, "local").mockImplementation(() => {
        return {
          toISODate: () => now,
        };
      });
    });

    afterAll(() => {
      spy.mockRestore();
    });

    it("sets has_future_child_date as true for future birth bonding leave", () => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason(future).create();

      render();
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          child_birth_date: future,
          child_placement_date: null,
          has_future_child_date: true,
        },
      });
    });

    it("sets has_future_child_date as false for past birth bonding leave", () => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason(past).create();

      render();
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          child_birth_date: past,
          child_placement_date: null,
          has_future_child_date: false,
        },
      });
    });

    it("sets has_future_child_date as true for future placement bonding leave", () => {
      claim = new MockClaimBuilder()
        .bondingFosterCareLeaveReason(future)
        .create();

      render();
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          child_birth_date: null,
          child_placement_date: future,
          has_future_child_date: true,
        },
      });
    });

    it("sets has_future_child_date as false for past placement bonding leave", () => {
      claim = new MockClaimBuilder()
        .bondingFosterCareLeaveReason(past)
        .create();

      render();
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          child_birth_date: null,
          child_placement_date: past,
          has_future_child_date: false,
        },
      });
    });
  });
});
