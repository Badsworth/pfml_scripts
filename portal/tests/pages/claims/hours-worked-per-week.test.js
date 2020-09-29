import HoursWorkedPerWeek from "../../../src/pages/claims/hours-worked-per-week";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("HoursWorkedPerWeek", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    ({ appLogic, wrapper } = renderWithAppLogic(HoursWorkedPerWeek, {
      claimAttrs: {
        hours_worked_per_week: 40.5,
      },
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
