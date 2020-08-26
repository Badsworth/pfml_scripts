import Address from "../../../src/pages/claims/address";
import AddressModel from "../../../src/models/Address";
import pick from "lodash/pick";
import { renderWithAppLogic } from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("Address", () => {
  let appLogic, claim, residentialAddress, wrapper;

  beforeEach(() => {
    residentialAddress = new AddressModel({
      line_1: "19 Staniford St",
      line_2: "Suite 505",
      city: "Boston",
      state: "MA",
      zip: "02214",
    });

    ({ appLogic, claim, wrapper } = renderWithAppLogic(Address, {
      claimAttrs: {
        temp: {
          residential_address: residentialAddress,
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
        expect.any(String),
        pick(claim, ["temp.residential_address"])
      );
    });
  });
});
