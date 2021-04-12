import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import Ssn from "../../../src/pages/applications/ssn";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(Ssn, {
    claimAttrs,
  });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("Ssn", () => {
  it("renders the form", () => {
    const { wrapper } = setup({
      // API returns the tax_identifier with only the last 4 digits
      tax_identifier: "*****1234",
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update when the form is submitted", async () => {
    const { appLogic, claim, changeField, submitForm } = setup({
      tax_identifier: "*****1234",
    });

    // Existing data
    await submitForm();
    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        tax_identifier: claim.tax_identifier,
      }
    );

    // New changes
    changeField("tax_identifier", "123-12-3123");
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        tax_identifier: "123-12-3123",
      }
    );
  });
});
