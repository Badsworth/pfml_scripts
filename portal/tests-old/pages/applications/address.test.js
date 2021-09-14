import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import Address from "../../../src/pages/applications/address";
import AddressModel from "../../../src/models/Address";
import { act } from "react-dom/test-utils";

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
      changeRadioGroup("has_mailing_address", "false");
    });

    it("hides conditional content", () => {
      expect(wrapper.find("ConditionalContent").props().visible).toBeFalsy();
    });

    it("submits residential address", () => {
      wrapper.find("QuestionPage").simulate("save");
      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          residential_address: testAddress,
          has_mailing_address: false,
          mailing_address: null,
        }
      );
    });

    describe("When user has a different mailing address", () => {
      beforeEach(() => {
        changeRadioGroup("has_mailing_address", "true");
      });

      it("shows mailing address fields", () => {
        expect(wrapper.find("ConditionalContent").props().visible).toBe(true);
      });

      it("submits both address info", () => {
        const { changeField } = simulateEvents(wrapper);
        changeField("mailing_address", testAddress);
        wrapper.find("QuestionPage").simulate("save");

        expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
          expect.any(String),
          {
            residential_address: testAddress,
            mailing_address: testAddress,
            has_mailing_address: true,
          }
        );
      });

      describe("when user chooses they have a mailing address ", () => {
        beforeEach(() => {
          ({ appLogic, wrapper } = renderWithAppLogic(Address, {
            claimAttrs: {
              residential_address: null,
              mailing_address: null,
            },
            render: "mount", // support useEffect
          }));

          ({ changeRadioGroup } = simulateEvents(wrapper));
          changeRadioGroup("has_mailing_address", "true");
        });

        it("submits without mailing address info", async () => {
          await act(async () => {
            await wrapper.find("form").simulate("submit");
          });

          expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
            expect.any(String),
            {
              mailing_address: {},
              has_mailing_address: true,
            }
          );
        });

        it("submits when user changes the answer back to not have a mailing address", async () => {
          changeRadioGroup("has_mailing_address", "false");

          await act(async () => {
            await wrapper.find("form").simulate("submit");
          });

          expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
            expect.any(String),
            {
              mailing_address: null,
              has_mailing_address: false,
            }
          );
        });
      });
    });
  });
});
