import DateOfChild from "../../../../src/pages/claims/bonding/date-of-child";
import pick from "lodash/pick";
import { renderWithAppLogic } from "../../../test-utils";

jest.mock("../../../../src/hooks/useAppLogic");

describe("DateOfChild", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(DateOfChild, {
      claimAttrs: {
        temp: {
          leave_details: {
            bonding: {
              date_of_child: "2020-08-01",
            },
          },
        },
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
        pick(claim, ["temp.leave_details.bonding.date_of_child"]),
        expect.any(Array)
      );
    });
  });
});
