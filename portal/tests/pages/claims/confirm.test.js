import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import Confirm from "../../../src/pages/claims/confirm";

jest.mock("../../../src/hooks/useAppLogic");

describe("Confirm", () => {
  let appLogic, claim, submitForm, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(Confirm));
    ({ submitForm } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user clicks agree and submit", () => {
    it("calls submitApplication", () => {
      submitForm();
      expect(appLogic.claims.submit).toHaveBeenCalledWith(claim.application_id);
    });
  });
});
