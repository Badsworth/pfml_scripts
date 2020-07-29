import DateOfBirth from "../../../src/pages/claims/date-of-birth";
import pick from "lodash/pick";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("DateOfBirth", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(DateOfBirth, {
      claimAttrs: {
        date_of_birth: "2019-02-28",
      },
    }));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateClaim", () => {
      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.updateClaim).toHaveBeenCalledWith(
        expect.any(String),
        pick(claim, ["date_of_birth"])
      );
    });
  });
});
