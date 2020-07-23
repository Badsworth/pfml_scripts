import AverageWorkHours from "../../../src/pages/claims/average-work-hours";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("AverageWorkHours", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    ({ appLogic, wrapper } = renderWithAppLogic(AverageWorkHours, {
      claimAttrs: {
        temp: { leave_details: { avg_weekly_work_hours: "40" } },
      },
    }));
  });

  it("renders the form", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateClaim", () => {
      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.updateClaim).toHaveBeenCalledTimes(1);
    });
  });
});
