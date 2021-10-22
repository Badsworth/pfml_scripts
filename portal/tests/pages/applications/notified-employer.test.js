import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import NotifiedEmployer from "../../../src/pages/applications/notified-employer";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (claim) => {
  if (!claim) {
    claim = new MockBenefitsApplicationBuilder().create();
  }
  return renderPage(
    NotifiedEmployer,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("NotifiedEmployer", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("shows employer notification date question when user selects yes to having notified employer", async () => {
    setup();
    userEvent.click(screen.getByRole("radio", { name: "Yes" }));
    await waitFor(() => {
      expect(screen.getByText(/When did you tell them?/)).toBeInTheDocument();
    });
  });

  it("hides must notify employer warning when user selects yes to having notified employer", () => {
    setup();
    userEvent.click(screen.getByRole("radio", { name: "Yes" }));

    expect(
      screen.queryByText(
        /You can continue to enter information about your leave. Before you can submit your application, you must tell your employer that you’re taking$t(chars.nbsp)leave. Notify your employer at least 30 days before the start of your leave if possible./
      )
    ).not.toBeInTheDocument();
  });

  it("calls claims.update when user submits form with newly entered data", async () => {
    setup();

    userEvent.click(screen.getByRole("radio", { name: "Yes" }));
    const [monthInput, dayInput, yearInput] = screen.getAllByRole("textbox");
    userEvent.type(monthInput, "6");
    userEvent.type(dayInput, "25");
    userEvent.type(yearInput, "2020");
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          employer_notified: true,
          employer_notification_date: "2020-06-25",
        },
      });
    });
  });

  it("calls claims.update when user submits form with previously entered data", async () => {
    const claim = new BenefitsApplication({
      application_id: "mock_application_id",
      leave_details: {
        employer_notified: true,
        employer_notification_date: "2020-06-25",
      },
    });

    setup(claim);
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          employer_notified: true,
          employer_notification_date: "2020-06-25",
        },
      });
    });
  });

  describe("when user selects no to having notified employer", () => {
    it("hides employer notification date question", () => {
      setup();

      userEvent.click(screen.getByRole("radio", { name: "No" }));
      expect(
        screen.queryByRole("textbox", { name: "Year" })
      ).not.toBeInTheDocument();
    });

    it("shows must notify employer warning", () => {
      setup();

      userEvent.click(screen.getByRole("radio", { name: "No" }));

      expect(
        screen.getByText(
          /You can continue to enter information about your leave./
        )
      ).toBeInTheDocument();
    });
  });
});
