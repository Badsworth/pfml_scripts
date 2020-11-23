import OtherIncomes from "../../../src/pages/applications/other-incomes";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("OtherIncomes", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(OtherIncomes, {
      claimAttrs: { temp: { has_other_incomes: true } },
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
          temp: { has_other_incomes: claim.temp.has_other_incomes },
        }
      );
    });
  });
});
