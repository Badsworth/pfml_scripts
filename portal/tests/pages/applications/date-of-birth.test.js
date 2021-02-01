import DateOfBirth from "../../../src/pages/applications/date-of-birth";
import { pick } from "lodash";
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
    it("calls claims.update", () => {
      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        expect.any(String),
        pick(claim, ["date_of_birth"])
      );
    });
  });
});
