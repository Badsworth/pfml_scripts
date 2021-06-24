import { renderWithAppLogic, simulateEvents } from "../../../test-utils";
import AddOrganization from "../../../../src/pages/employers/organizations/add-organization";
import routes from "../../../../src/routes";

jest.mock("../../../../src/hooks/useAppLogic");

describe("AddOrganization", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    ({ wrapper, appLogic } = renderWithAppLogic(AddOrganization, {
      diveLevels: 1,
    }));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
    expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
  });

  it("submits FEIN", async () => {
    ({ changeField, submitForm } = simulateEvents(wrapper));
    changeField("ein", "012345678");
    await submitForm();

    expect(appLogic.employers.addEmployer).toHaveBeenCalledWith(
      {
        employer_fein: "012345678",
      },
      routes.employers.organizations
    );
  });
});
