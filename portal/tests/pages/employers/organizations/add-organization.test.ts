import { screen, waitFor } from "@testing-library/react";
import AddOrganization from "../../../../src/pages/employers/organizations/add-organization";
import { renderPage } from "../../../test-utils";
import routes from "../../../../src/routes";
import userEvent from "@testing-library/user-event";

const setup = () => {
  let addEmployerSpy;
  const utils = renderPage(AddOrganization, {
    addCustomSetup: (appLogic) => {
      addEmployerSpy = jest.spyOn(appLogic.employers, "addEmployer");
    },
  });
  return { addEmployerSpy, ...utils };
};
describe("AddOrganization", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("submits FEIN", async () => {
    const { addEmployerSpy } = setup();
    userEvent.type(screen.getByRole("textbox"), "01-2345678");
    userEvent.click(screen.getByRole("button", { name: "Continue" }));

    await waitFor(() => {
      expect(addEmployerSpy).toHaveBeenCalledWith(
        {
          employer_fein: "01-2345678",
        },
        routes.employers.organizations
      );
    });
  });
});
