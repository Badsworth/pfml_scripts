import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import { UserLeaveAdministrator } from "../../../src/models/User";
import VerifyBusiness from "../../../src/pages/employers/verify-business";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";

jest.mock("../../../src/hooks/useAppLogic");

describe("VerifyBusiness", () => {
  let changeField, submitForm;
  const query = {
    employer_id: "mock_employer_id",
    next: "/employers/applications/new-application/?absence_id=mock_absence_id",
  };
  mockRouter.pathname = routes.employers.VerifyBusiness;

  const { wrapper, appLogic } = renderWithAppLogic(VerifyBusiness, {
    diveLevels: 1,
    props: {
      query,
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

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  it("submits withholding data with correct values", async () => {
    ({ changeField, submitForm } = simulateEvents(wrapper));
    changeField("withholdingAmount", "123");
    await submitForm();

    expect(appLogic.employers.submitWithholding).toHaveBeenCalledWith(
      {
        employer_id: "mock_employer_id",
        withholding_amount: "123",
        withholding_quarter: "2020-10-10",
      },
      query.next
    );
  });
});
