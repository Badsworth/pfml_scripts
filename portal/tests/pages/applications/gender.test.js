import { screen, waitFor } from "@testing-library/react";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import Gender from "../../../src/pages/applications/gender";
import { pick } from "lodash";
import { renderPage } from "../../test-utils";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const defaultGender = {
  gender: "Woman",
};

const setup = (gender) => {
  const claimAttrs = {
    ...gender,
  };
  const claim = new BenefitsApplication({
    application_id: "mock_application_id",
    ...claimAttrs,
  });
  return renderPage(
    Gender,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic);
        appLogic.benefitsApplications.update = updateClaim;
        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([claim]);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("Gender", () => {
  it("renders the page", () => {
    const { container } = setup(defaultGender);
    expect(container).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    setup(defaultGender);

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(
        expect.any(String),
        pick(defaultGender, ["gender"])
      );
    });
  });

  it("calls claims.update when the form is successfully submitted with new data", async () => {
    setup({});

    userEvent.click(screen.getByRole("radio", { name: "Woman" }));

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(
        expect.any(String),
        pick(defaultGender, ["gender"])
      );
    });
  });
});
