import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import Address from "../../../src/pages/claims/address";
import AddressModel from "../../../src/models/Address";

jest.mock("../../../src/hooks/useAppLogic");

describe("Address", () => {
  let appLogic, wrapper;
  const testAddress = new AddressModel({
    line_1: "19 Staniford St",
    line_2: "Suite 505",
    city: "Boston",
    state: "MA",
    zip: "02214",
  });

  beforeEach(() => {
    ({ appLogic, wrapper } = renderWithAppLogic(Address, {
      claimAttrs: {
        residential_address: null,
        mailing_address: null,
      },
    }));
  });

  it("renders the page without any address info", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when residential address is available", () => {
    let changeField, changeRadioGroup;

    beforeEach(() => {
      ({ changeField, changeRadioGroup } = simulateEvents(wrapper));
      changeField("residential_address", testAddress);
      changeRadioGroup("temp.has_mailing_address", "false");
    });

    it("hides conditional content", () => {
      expect(wrapper.find("ConditionalContent").props().visible).toBeFalsy();
    });

    it("submits residential address", () => {
      wrapper.find("QuestionPage").simulate("save");
      expect(appLogic.claims.update).toHaveBeenCalledWith(expect.any(String), {
        residential_address: testAddress,
        temp: { has_mailing_address: false },
        mailing_address: null,
      });
    });

    describe("When user has a different mailing address", () => {
      beforeEach(() => {
        changeRadioGroup("temp.has_mailing_address", "true");
      });

      it("shows mailing address fields", () => {
        expect(wrapper.find("ConditionalContent").props().visible).toBe(true);
      });

      it("submits both address info", () => {
        const { changeField } = simulateEvents(wrapper);
        changeField("mailing_address", testAddress);
        wrapper.find("QuestionPage").simulate("save");

        expect(appLogic.claims.update).toHaveBeenCalledWith(
          expect.any(String),
          {
            residential_address: testAddress,
            mailing_address: testAddress,
            temp: { has_mailing_address: true },
          }
        );
      });
    });
  });
});
