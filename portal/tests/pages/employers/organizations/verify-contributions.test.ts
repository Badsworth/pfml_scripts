import User, { UserLeaveAdministrator } from "../../../../src/models/User";
import { screen, waitFor } from "@testing-library/react";
import VerifyContributions from "../../../../src/pages/employers/organizations/verify-contributions";
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
        appLogic.employers.loadWithholding = jest.fn().mockResolvedValue({
          filing_period: "2011-11-20",
        });
        submitWithholdingSpy = jest.spyOn(
          appLogic.employers,
          "submitWithholding"
        );
      },
    },
    {
      query,
      ...props,
    }
  );
  return { submitWithholdingSpy, ...utils };
};

describe("VerifyContributions", () => {
  it("renders the page", async () => {
    const { container } = setup();

    await waitFor(() => {
      expect(
        screen.getByText(/Verify your paid leave contributions/)
      ).toBeInTheDocument();
    });

    expect(container.firstChild).toMatchSnapshot();
  });

  it("submits withholding data with correct values", async () => {
    const { submitWithholdingSpy } = setup();
    userEvent.type(await screen.findByRole("textbox"), "1,234.560");
    userEvent.click(await screen.findByRole("button", { name: "Submit" }));

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
    userEvent.type(await screen.findByRole("textbox"), "invalid");
    userEvent.click(await screen.findByRole("button", { name: "Submit" }));

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
