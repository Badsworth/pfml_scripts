import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import ConsentToDataSharing from "../../../src/pages/user/consent-to-data-sharing";
import { UserRole } from "../../../src/models/User";
import routes from "../../../src/routes";

jest.mock("../../../src/hooks/useAppLogic");

describe("ConsentToDataSharing", () => {
  let appLogic, wrapper;
  const user_id = "mock-user-id";

  const renderWithUserParams = (user) => {
    ({ appLogic, wrapper } = renderWithAppLogic(ConsentToDataSharing, {
      diveLevels: 1,
      userAttrs: { ...user },
    }));
    appLogic.portalFlow.pathName = routes.user.consentToDataSharing;
  };

  beforeEach(() => {
    renderWithUserParams({ user_id });
  });

  it("shows the correct content for non-employers", () => {
    expect(wrapper.find("AccordionItem").at(0).prop("heading")).toEqual(
      "Applying for benefits"
    );
    expect(wrapper).toMatchSnapshot();
  });

  it("shows the correct contents for employers", () => {
    renderWithUserParams({
      user_id,
      roles: [new UserRole({ role_description: "Employer" })],
    });

    expect(wrapper.find("AccordionItem").at(0).prop("heading")).toEqual(
      "Reviewing paid leave applications"
    );
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the user agrees and submits the form", () => {
    beforeEach(async () => {
      const { submitForm } = simulateEvents(wrapper);
      await submitForm();
    });

    it("sets user's consented_to_data_sharing field to true", () => {
      expect(appLogic.users.updateUser).toHaveBeenCalledWith(user_id, {
        consented_to_data_sharing: true,
      });
    });
  });
});
