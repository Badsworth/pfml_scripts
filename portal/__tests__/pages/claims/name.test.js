import Name from "../../../src/pages/claims/name";
import pick from "lodash/pick";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("Name", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(Name, {
      claimAttrs: {
        first_name: "Aquib",
        middle_name: "cricketer",
        last_name: "Khan",
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
        pick(claim, ["first_name", "last_name"])
      );
    });
  });
});
