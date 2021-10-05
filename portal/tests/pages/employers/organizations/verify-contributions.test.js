import User, { UserLeaveAdministrator } from "../../../../src/models/User";
import { screen, waitFor } from "@testing-library/react";
import { VerifyContributions } from "../../../../src/pages/employers/organizations/verify-contributions";
import Withholding from "../../../../src/models/Withholding";
import { renderPage } from "../../../test-utils";
import userEvent from "@testing-library/user-event";

const query = {
  employer_id: "mock_employer_id",
  next: "/employers/applications/new-application/?absence_id=mock_absence_id",
};

const setup = (props = {}) => {
  let submitWithholdingSpy;
  const utils = renderPage(
    VerifyContributions,
    {
      addCustomSetup: (appLogic) => {
        appLogic.users.user = new User({
          consented_to_data_sharing: true,
          user_leave_administrators: [
            new UserLeaveAdministrator({
              employer_dba: "Company Name",
              employer_fein: "12-3456789",
              employer_id: "mock_employer_id",
              verified: false,
            }),
          ],
        });
        submitWithholdingSpy = jest.spyOn(
          appLogic.employers,
          "submitWithholding"
        );
      },
    },
    {
      query,
      withholding: new Withholding({
        filing_period: "2011-11-20",
      }),
      ...props,
    }
  );
  return { submitWithholdingSpy, ...utils };
};

describe("VerifyContributions", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("submits withholding data with correct values", async () => {
    const { submitWithholdingSpy } = setup();
    userEvent.type(screen.getByRole("textbox"), "1,234.560");
    userEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(submitWithholdingSpy).toHaveBeenCalledWith(
        {
          employer_id: "mock_employer_id",
          withholding_amount: 1234.56,
          withholding_quarter: "2011-11-20",
        },
        query.next
      );
    });
  });

  it("submits withholding data as 0 if input is invalid", async () => {
    const { submitWithholdingSpy } = setup();
    userEvent.type(screen.getByRole("textbox"), "invalid");
    userEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(submitWithholdingSpy).toHaveBeenCalledWith(
        {
          employer_id: "mock_employer_id",
          withholding_amount: 0,
          withholding_quarter: "2011-11-20",
        },
        query.next
      );
    });
  });
});
