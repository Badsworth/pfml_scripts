import { renderWithAppLogic, simulateEvents } from "../../../test-utils";
import { UserLeaveAdministrator } from "../../../../src/models/User";
import { VerifyContributions } from "../../../../src/pages/employers/organizations/verify-contributions";
import Withholding from "../../../../src/models/Withholding";
import { mockRouter } from "next/router";
import routes from "../../../../src/routes";

jest.mock("../../../../src/hooks/useAppLogic");

describe("VerifyContributions", () => {
  let appLogic, changeField, submitForm, wrapper;
  const query = {
    employer_id: "mock_employer_id",
    next: "/employers/applications/new-application/?absence_id=mock_absence_id",
  };
  mockRouter.pathname = routes.employers.verifyContributions;

  function render() {
    return renderWithAppLogic(VerifyContributions, {
      diveLevels: 0,
      props: {
        query,
        withholding: new Withholding({
          filing_period: "2011-11-20",
        }),
      },
      userAttrs: {
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Company Name",
            employer_fein: "11-111111",
            employer_id: "mock_employer_id",
            verified: false,
          }),
        ],
      },
    });
  }

  beforeEach(() => {
    ({ wrapper, appLogic } = render());
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  it("submits withholding data with correct values", async () => {
    ({ changeField, submitForm } = simulateEvents(wrapper));
    changeField("withholdingAmount", "1,234.560");
    await submitForm();

    expect(appLogic.employers.submitWithholding).toHaveBeenCalledWith(
      {
        employer_id: "mock_employer_id",
        withholding_amount: 1234.56,
        withholding_quarter: "2011-11-20",
      },
      query.next
    );
  });

  it("submits withholding data as 0 if input is invalid", async () => {
    ({ changeField, submitForm } = simulateEvents(wrapper));
    changeField("withholdingAmount", null);
    await submitForm();

    expect(appLogic.employers.submitWithholding).toHaveBeenCalledWith(
      {
        employer_id: "mock_employer_id",
        withholding_amount: 0,
        withholding_quarter: "2011-11-20",
      },
      query.next
    );
  });
});
