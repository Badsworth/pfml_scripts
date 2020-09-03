import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import DateOfChild from "../../../src/pages/claims/date-of-child";
import { act } from "react-dom/test-utils";
import pick from "lodash/pick";

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
    it("shows the correct input question", () => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
      render();
      expect(wrapper.find({ name: child_birth_date }).exists()).toBeTruthy();
      expect(wrapper.find({ name: child_placement_date }).exists()).toBeFalsy();
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

  describe("when the form is successfully submitted", () => {
    it("calls claims.update for new born", () => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
      render();
      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        expect.any(String),
        pick(claim, [child_birth_date, child_placement_date])
      );
    });
  });
});
