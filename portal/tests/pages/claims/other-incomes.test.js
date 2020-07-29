import OtherIncomes from "../../../src/pages/claims/other-incomes";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("OtherIncomes", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomes, {
      claimAttrs: { has_other_incomes: true },
    }));
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
        has_other_incomes: claim.has_other_incomes,
      });
    });
  });
});
