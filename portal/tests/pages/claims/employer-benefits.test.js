import EmployerBenefits from "../../../src/pages/claims/employer-benefits";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefits", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(EmployerBenefits));
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
          has_employer_benefits: claim.has_employer_benefits,
        },
        expect.any(Array)
      );
    });
  });
});
