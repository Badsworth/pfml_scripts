import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../../src/models/PaymentPreference";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import PaymentMethod from "../../../src/pages/applications/payment-method";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = () => {
  const claim = new MockBenefitsApplicationBuilder().part1Complete().create();
  let submitPaymentPreferenceSpy;

  const utils = renderPage(
    PaymentMethod,
    {
      addCustomSetup: (appLogic) => {
        submitPaymentPreferenceSpy = jest.spyOn(
          appLogic.benefitsApplications,
          "submitPaymentPreference"
        );
        setupBenefitsApplications(appLogic, [claim]);
      },
    },
    {
      query: { claim_id: claim.application_id },
    }
  );

  return {
    submitPaymentPreferenceSpy,
    ...utils,
  };
};

describe("PaymentMethod", () => {
  it("renders the page", () => {
    const { container } = setup();

    expect(container).toMatchSnapshot();
  });

  it("displays the Direct Deposit fieldset when Direct Deposit is selected", () => {
    const fieldsetTextMatch = /Enter your bank account information/i;

    setup();
    userEvent.click(
      screen.getByRole("radio", {
        name: /Direct deposit into my bank account/i,
      })
    );

    expect(
      screen.queryByRole("group", { name: fieldsetTextMatch })
    ).toBeInTheDocument();

    userEvent.click(
      screen.getByRole("radio", {
        name: /Paper/i,
      })
    );

    expect(
      screen.queryByRole("group", { name: fieldsetTextMatch })
    ).not.toBeInTheDocument();
  });

  it("renders a warning when a routing-like account number is entered", () => {
    setup();

    userEvent.click(
      screen.getByRole("radio", {
        name: /Direct deposit into my bank account/i,
      })
    );
    expect(
      screen.queryByText(
        /Your account number looks similar to a routing number/
      )
    ).not.toBeInTheDocument();

    userEvent.type(
      screen.getByRole("textbox", { name: "Account number" }),
      "121000358"
    );
    expect(
      screen.getByText(/Your account number looks similar to a routing number/)
    ).toBeInTheDocument();

    userEvent.type(
      screen.getByRole("textbox", { name: "Account number" }),
      "987654321" // typical account number
    );
    userEvent.click(
      screen.getByRole("radio", {
        name: /Checking/i,
      })
    );
    expect(
      screen.queryByText(
        /Your account number looks similar to a routing number/
      )
    ).not.toBeInTheDocument();
  });

  it("throws an error when the account number has not been retyped", async () => {
    setup();
    const account_number = "987654321";
    const routing_number = "123456789";

    userEvent.click(
      screen.getByRole("radio", {
        name: /Direct deposit into my bank account/i,
      })
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /Routing number/i }),
      routing_number
    );
    userEvent.type(
      screen.getByRole("textbox", { name: "Account number" }),
      account_number
    );
    userEvent.click(
      screen.getByRole("radio", {
        name: /Checking/i,
      })
    );

    userEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Retype your account number/)
      ).toBeInTheDocument();
    });
  });

  it("throws an error when the retyped account number and account number do not match", async () => {
    setup();
    const account_number = "987654321";
    const routing_number = "123456789";

    userEvent.click(
      screen.getByRole("radio", {
        name: /Direct deposit into my bank account/i,
      })
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /Routing number/i }),
      routing_number
    );
    userEvent.type(
      screen.getByRole("textbox", { name: "Account number" }),
      account_number
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /Retype account number/i }),
      "1111111111"
    );
    userEvent.click(
      screen.getByRole("radio", {
        name: /Checking/i,
      })
    );

    userEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(
        screen.getByText(
          /The account numbers you entered do not match. Make sure the numbers are exactly the same./
        )
      ).toBeInTheDocument();
    });
  });

  it("submits direct deposit answers", async () => {
    const { submitPaymentPreferenceSpy } = setup();
    const account_number = "987654321";
    const routing_number = "123456789";

    userEvent.click(
      screen.getByRole("radio", {
        name: /Direct deposit into my bank account/i,
      })
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /Routing number/i }),
      routing_number
    );
    userEvent.type(
      screen.getByRole("textbox", { name: "Account number" }),
      account_number
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /Retype account number/i }),
      account_number
    );
    userEvent.click(
      screen.getByRole("radio", {
        name: /Checking/i,
      })
    );

    userEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(submitPaymentPreferenceSpy).toHaveBeenCalledWith(
        expect.any(String),
        {
          payment_preference: {
            account_number,
            bank_account_type: BankAccountType.checking,
            routing_number,
            payment_method: PaymentPreferenceMethod.ach,
            retype_account_number: account_number,
          },
        }
      );
    });
  });

  it("submits paper check answers", async () => {
    const { submitPaymentPreferenceSpy } = setup();

    userEvent.click(
      screen.getByRole("radio", {
        name: /Paper check/i,
      })
    );

    userEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(submitPaymentPreferenceSpy).toHaveBeenCalledWith(
        expect.any(String),
        {
          payment_preference: {
            account_number: null,
            bank_account_type: null,
            routing_number: null,
            payment_method: PaymentPreferenceMethod.check,
            retype_account_number: null,
          },
        }
      );
    });
  });
});
