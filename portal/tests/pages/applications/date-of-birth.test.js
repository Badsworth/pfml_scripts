import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import DateOfBirth from "../../../src/pages/applications/date-of-birth";
import { pick } from "lodash";

jest.mock("../../../src/hooks/useAppLogic");

const DATE_OF_BIRTH = "2019-02-28";

describe("DateOfBirth", () => {
  let appLogic, claim, wrapper;

  const render = (claimAttrs = {}) => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(DateOfBirth, {
      claimAttrs,
    }));
  };

  it("renders the page", () => {
    render({ date_of_birth: DATE_OF_BIRTH });
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with newly-entered data", () => {
    render();
    const { changeField } = simulateEvents(wrapper);
    changeField("date_of_birth", DATE_OF_BIRTH);
    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      expect.any(String),
      {
        date_of_birth: DATE_OF_BIRTH,
      }
    );
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", () => {
    render({ date_of_birth: DATE_OF_BIRTH });
    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      expect.any(String),
      pick(claim, ["date_of_birth"])
    );
  });
});
