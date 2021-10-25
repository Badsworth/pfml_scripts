import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import DateOfBirth from "../../../src/pages/applications/date-of-birth";
import { pick } from "lodash";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const DATE_OF_BIRTH = "2019-02-28";

describe("DateOfBirth", () => {
  const render = (claim) => {
    if (!claim) {
      claim = new MockBenefitsApplicationBuilder().create();
    }
    return renderPage(
      DateOfBirth,
      {
        addCustomSetup: (appLogic) => {
          appLogic.benefitsApplications.update = updateClaim;
          appLogic.benefitsApplications.benefitsApplications =
            new BenefitsApplicationCollection([claim]);
        },
      },
      { query: { claim_id: "mock_application_id" }, claim: {} }
    );
  };

  it("renders the page", () => {
    const { container } = render();
    expect(container).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with newly-entered data", async () => {
    render();

    userEvent.type(
      screen.getByRole("textbox", {
        name: "Month",
      }),
      "2"
    );
    userEvent.type(
      screen.getByRole("textbox", {
        name: "Day",
      }),
      "28"
    );
    userEvent.type(
      screen.getByRole("textbox", {
        name: "Year",
      }),
      "2019"
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(expect.any(String), {
        date_of_birth: DATE_OF_BIRTH,
      });
    });
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    const claim = new MockBenefitsApplicationBuilder().create({
      date_of_birth: DATE_OF_BIRTH,
    });
    render(claim);
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(
        expect.any(String),
        pick(claim, ["date_of_birth"])
      );
    });
  });
});
