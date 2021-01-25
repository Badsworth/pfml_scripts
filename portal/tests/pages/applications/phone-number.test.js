import PhoneNumber from "../../../src/pages/applications/phone-number";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("PhoneNumber", () => {
  let appLogic, claim, wrapper;

  beforeEach(() => {
    ({ appLogic, claim, wrapper } = renderWithAppLogic(PhoneNumber, {
      claimAttrs: {
        phone: {
          phone_number: "123-456-7890",
          phone_type: "cell",
        },
      },
    }));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls claims.update", () => {
      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          phone: {
            int_code: "1",
            phone_number: "123-456-7890",
            phone_type: "cell",
          },
        }
      );
    });
  });
});
