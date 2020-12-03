import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import EmployerBenefits from "../../../src/pages/applications/employer-benefits";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("EmployerBenefits", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    claim = new MockClaimBuilder().continuous().create();

    ({ appLogic, wrapper } = renderWithAppLogic(EmployerBenefits, {
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
          temp: { has_employer_benefits: claim.temp.has_employer_benefits },
        }
      );
    });
  });
});
