import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import PhoneNumber from "../../../src/pages/applications/phone-number";
import { PhoneType } from "../../../src/models/BenefitsApplication";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = (claim = new MockBenefitsApplicationBuilder().create()) => {
  let updateSpy;

  const utils = renderPage(
    PhoneNumber,
    {
      addCustomSetup: (appLogic) => {
        updateSpy = jest.spyOn(appLogic.benefitsApplications, "update");
        setupBenefitsApplications(appLogic, [claim]);
      },
    },
    {
      query: { claim_id: claim.application_id },
    }
  );

  return {
    updateSpy,
    ...utils,
  };
};

describe("PhoneNumber", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("submits form with existing data", async () => {
    const claim = new MockBenefitsApplicationBuilder().part1Complete().create();
    const { updateSpy } = setup(claim);

    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(claim.application_id, {
        phone: {
          int_code: "1",
          phone_number: claim.phone.phone_number,
          phone_type: claim.phone.phone_type,
        },
      });
    });
  });

  it("submits form with newly entered data", async () => {
    const { updateSpy } = setup();

    userEvent.type(
      screen.getByRole("textbox", { name: /phone number/i }),
      "123-456-7890"
    );
    userEvent.click(screen.getByRole("radio", { name: /mobile/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        phone: {
          int_code: "1",
          phone_number: "123-456-7890",
          phone_type: PhoneType.cell,
        },
      });
    });
  });
});
