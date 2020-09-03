import Ssn from "../../../src/pages/claims/ssn";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("Ssn", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    ({ appLogic, wrapper } = renderWithAppLogic(Ssn, {
      claimAttrs: { tax_identifier: "123-123-1234" },
    }));
  });

  it("renders the form", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls claims.update", () => {
      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledTimes(1);
    });
  });
});
