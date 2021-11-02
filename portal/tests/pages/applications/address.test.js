import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import Address from "../../../src/pages/applications/address";
import AddressModel from "../../../src/models/Address";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import { rest } from "msw";
import { setupServer } from "msw/node";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

describe("Address", () => {
  const update = jest.fn(() => {
    return Promise.resolve();
  });
  const address = new AddressModel({
    line_1: "19 Staniford St",
    line_2: "Suite 505",
    city: "Boston",
    state: "MA",
    zip: "02214",
  });
  const claim_id = "mock_application_id";

  const render = () => {
    const options = {
      addCustomSetup: (appLogic) => {
        appLogic.benefitsApplications.update = update;
        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([
            new MockBenefitsApplicationBuilder({
              residential_address: null,
              mailing_address: null,
            }).create(),
          ]);
      },
      isLoggedIn: true,
    };
    return renderPage(Address, options, { query: { claim_id } });
  };

  it("renders the page without any address info", () => {
    const { container } = render();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("enables user to submit residential address", async () => {
    const fillAddress = () => {
      userEvent.type(
        screen.getByRole("textbox", { name: "Address" }),
        address.line_1
      );
      userEvent.type(
        screen.getByRole("textbox", { name: "Address line 2 (optional)" }),
        address.line_2
      );
      userEvent.type(
        screen.getByRole("textbox", { name: "City" }),
        address.city
      );
      userEvent.selectOptions(
        screen.getByRole("combobox", { name: "State" }),
        address.state
      );
      userEvent.type(screen.getByRole("textbox", { name: "ZIP" }), address.zip);
    };

    render();
    userEvent.click(screen.getByRole("radio", { name: "Yes" }));
    fillAddress();
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        residential_address: address,
        has_mailing_address: false,
        mailing_address: null,
      });
    });
  });

  it("mailing address is hidden when not required", () => {
    render();
    expect(
      screen.queryByText(/What is your mailing address?/)
    ).not.toBeInTheDocument();
  });

  it("shows mailing address fields when indicated", () => {
    render();
    userEvent.click(
      screen.getByRole("radio", {
        name: "No, I would like to add a mailing address",
      })
    );
    expect(
      screen.queryByText(/What is your mailing address?/)
    ).toBeInTheDocument();
  });

  it("can submit both residential and mailing address", async () => {
    render();
    userEvent.click(
      screen.getByRole("radio", {
        name: "No, I would like to add a mailing address",
      })
    );

    const residentialAddress2 = screen.getByRole("textbox", {
      name: "Address line 2 (optional)",
    });
    const residentialAddress = screen.getByRole("textbox", { name: "Address" });
    const mailingAddress = screen.getByRole("textbox", {
      name: "Mailing address",
    });
    const mailingAddress2 = screen.getByRole("textbox", {
      name: "Mailing address line 2 (optional)",
    });
    const [residentialCity, mailingCity] = screen.getAllByRole("textbox", {
      name: "City",
    });
    const [residentialState, mailingState] = screen.getAllByRole("combobox", {
      name: "State",
    });
    const [residentialZIP, mailingZIP] = screen.getAllByRole("textbox", {
      name: "ZIP",
    });

    userEvent.type(mailingAddress, address.line_1);
    userEvent.type(mailingAddress2, address.line_2);
    userEvent.type(residentialAddress, address.line_1);
    userEvent.type(residentialAddress2, address.line_2);
    userEvent.type(residentialCity, address.city);
    userEvent.type(mailingCity, address.city);
    userEvent.selectOptions(residentialState, address.state);
    userEvent.selectOptions(mailingState, address.state);
    userEvent.type(residentialZIP, address.zip);
    userEvent.type(mailingZIP, address.zip);

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        residential_address: address,
        mailing_address: address,
        has_mailing_address: true,
      });
    });
  });

  it("when a user chooses yes to mailing address, they can submit without mailing address", async () => {
    render();
    userEvent.click(
      screen.getByRole("radio", {
        name: "No, I would like to add a mailing address",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(
        claim_id,
        expect.objectContaining({
          mailing_address: {},
          has_mailing_address: true,
        })
      );
    });
  });

  it("submits when user changes the answer back to not have a mailing address", async () => {
    render();
    userEvent.click(
      screen.getByRole("radio", {
        name: "No, I would like to add a mailing address",
      })
    );
    userEvent.click(screen.getByRole("radio", { name: "Yes" }));
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(
        claim_id,
        expect.objectContaining({
          mailing_address: null,
          has_mailing_address: false,
        })
      );
    });
  });

  describe("address formatting when claimantValidateAddress feature flag is enabled", () => {
    const formattedAddress = new AddressModel({
      line_1: "FORMATTED 54321 Mock Address",
      line_2: "",
      city: "Washington",
      state: "DC",
      zip: "20005",
    });

    const unformattedAddress = new AddressModel({
      line_1: "54321 Mock Address",
      line_2: "",
      city: "Washington",
      state: "DC",
      zip: "20005",
    });

    const server = setupServer(
      rest.get(
        "https://api.experianaperture.io/address/format/v1/:addressKey",
        (req, res, ctx) => {
          return res(
            ctx.json({
              result: {
                global_address_key: req.params.addressKey,
                confidence: "Verified match",
                address: {
                  address_line_1: formattedAddress.line_1,
                  address_line_2: formattedAddress.line_2,
                  locality: formattedAddress.city,
                  region: formattedAddress.state,
                  postal_code: formattedAddress.zip,
                  country: "US",
                },
              },
            })
          );
        }
      )
    );

    const renderWithAddresses = (address = unformattedAddress) => {
      const benefitsApplication = new MockBenefitsApplicationBuilder().create();
      benefitsApplication.mailing_address = address;
      benefitsApplication.residential_address = address;
      benefitsApplication.has_mailing_address = true;
      let appLogic;

      const options = {
        addCustomSetup: (appLogicHook) => {
          appLogic = appLogicHook;
          appLogicHook.benefitsApplications.update = update;
          appLogicHook.benefitsApplications.benefitsApplications =
            new BenefitsApplicationCollection([benefitsApplication]);
        },
        isLoggedIn: true,
      };

      const view = renderPage(Address, options, { query: { claim_id } });
      return {
        appLogic,
        ...view,
      };
    };

    beforeAll(() => {
      server.listen();
    });
    beforeEach(() => {
      process.env.featureFlags = {
        claimantValidateAddress: true,
      };
    });

    afterAll(() => {
      process.env.featureFlags = {};
      server.close();
    });
    afterEach(() => server.resetHandlers());

    it("does not format masked addresses", async () => {
      const maskedAddress = new AddressModel({
        line_1: "*******",
      });
      renderWithAddresses(maskedAddress);

      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );

      await waitFor(() => {
        expect(update).toHaveBeenCalledWith(claim_id, {
          residential_address: maskedAddress,
          has_mailing_address: true,
          mailing_address: maskedAddress,
        });
      });
    });

    describe("when validation service returns 1 valid address", () => {
      const responseData = {
        result: {
          confidence: "Verified match",
          more_results_available: false,
          suggestions: [
            {
              global_address_key: "mockaddresskey",
              matched: [],
              text: "54321 Mock Address Washington, DC 20005",
              format:
                "https://api.experianaperture.io/address/format/v1/mockaddresskey",
            },
          ],
        },
      };

      beforeEach(() => {
        server.use(
          rest.post(
            "https://api.experianaperture.io/address/search/v1",
            (req, res, ctx) => {
              return res(ctx.json(responseData));
            }
          )
        );
      });

      it("updates with formatted address to API when user clicks save and continue", async () => {
        renderWithAddresses();

        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );

        await waitFor(() => {
          expect(update).toHaveBeenCalledWith(claim_id, {
            residential_address: formattedAddress,
            has_mailing_address: true,
            mailing_address: formattedAddress,
          });
        });
      });
    });

    describe("when validation service returns multiple valid addresses", () => {
      const responseData = {
        result: {
          confidence: "Multiple matches",
          more_results_available: false,
          suggestions: [
            {
              global_address_key: "mockaddresskeyapt1",
              matched: [],
              text: "54321 Mock Address Apt 1 Washington, DC 20005",
              format:
                "https://api.experianaperture.io/address/format/v1/mockaddresskeyapt1",
            },
            {
              global_address_key: "mockaddresskeyapt2",
              matched: [],
              text: "54321 Mock Address Apt 2 Washington, DC 20005",
              format:
                "https://api.experianaperture.io/address/format/v1/mockaddresskeyapt2",
            },
          ],
        },
      };

      beforeEach(() => {
        server.use(
          rest.post(
            "https://api.experianaperture.io/address/search/v1",
            (req, res, ctx) => {
              return res(ctx.json(responseData));
            }
          )
        );
      });

      it("does not update API and shows address suggestions when user clicks save and continue", async () => {
        const { appLogic } = renderWithAddresses();

        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );

        const residentialInput = await screen.findByTestId(
          "residential-address-error"
        );
        const mailingInput = await screen.findByTestId("mailing-address-error");
        expect(residentialInput).toMatchSnapshot();
        expect(mailingInput).toMatchSnapshot();
        expect(update).not.toHaveBeenCalled();
        expect(appLogic.catchError).toHaveBeenCalled();
      });

      describe("after user clicks save and continue", () => {
        beforeEach(() => {
          renderWithAddresses();
          userEvent.click(
            screen.getByRole("button", { name: "Save and continue" })
          );
        });

        it("updates with formatted address when user selects a suggestion then clicks save and continue", async () => {
          await screen.findByTestId("residential-address-error");
          await screen.findByTestId("mailing-address-error");

          const selection = screen.getAllByLabelText(
            responseData.result.suggestions[1].text
          );
          userEvent.click(selection[0]);
          userEvent.click(selection[1]);
          userEvent.click(
            screen.getByRole("button", { name: "Save and continue" })
          );

          await waitFor(() => {
            expect(update).toHaveBeenCalledWith(claim_id, {
              residential_address: formattedAddress,
              has_mailing_address: true,
              mailing_address: formattedAddress,
            });
          });
        });

        it("updates with entered addess when user selects entered address", async () => {
          await screen.findByTestId("residential-address-error");
          await screen.findByTestId("mailing-address-error");

          const selection = screen.getAllByText(unformattedAddress.toString());
          userEvent.click(selection[0]);
          userEvent.click(selection[1]);
          userEvent.click(
            screen.getByRole("button", { name: "Save and continue" })
          );

          await waitFor(() => {
            expect(update).toHaveBeenCalledWith(claim_id, {
              residential_address: unformattedAddress,
              has_mailing_address: true,
              mailing_address: unformattedAddress,
            });
          });
        });

        it("removes suggestions when user clicks Edit address", async () => {
          await screen.findByTestId("residential-address-error");
          await screen.findByTestId("mailing-address-error");

          const selection = screen.getAllByText("Edit address");

          userEvent.click(selection[0]);
          userEvent.click(selection[1]);

          await waitFor(() => {
            expect(
              screen.queryByTestId("residential-address-error")
            ).not.toBeInTheDocument();
            expect(
              screen.queryByTestId("mailing-address-error")
            ).not.toBeInTheDocument();
          });
        });
      });
    });

    describe("when validation service returns no valid addresses", () => {
      const responseData = {
        result: {
          confidence: "No matches",
          more_results_available: false,
          suggestions: [],
        },
      };

      beforeEach(() => {
        server.use(
          rest.post(
            "https://api.experianaperture.io/address/search/v1",
            (req, res, ctx) => {
              return res(ctx.json(responseData));
            }
          )
        );
      });

      it("does not update API and shows address suggestions", async () => {
        const { appLogic } = renderWithAddresses();

        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );

        const residentialInput = await screen.findByTestId(
          "residential-address-error"
        );
        const mailingInput = await screen.findByTestId("mailing-address-error");
        expect(residentialInput).toMatchSnapshot();
        expect(mailingInput).toMatchSnapshot();
        expect(update).not.toHaveBeenCalled();
        expect(appLogic.catchError).toHaveBeenCalled();
      });

      describe("after user clicks save and continue", () => {
        beforeEach(() => {
          renderWithAddresses();
          userEvent.click(
            screen.getByRole("button", { name: "Save and continue" })
          );
        });

        it("updates with entered addess when user selects entered address", async () => {
          await screen.findByTestId("residential-address-error");
          await screen.findByTestId("mailing-address-error");

          const selection = screen.getAllByText(unformattedAddress.toString());
          userEvent.click(selection[0]);
          userEvent.click(selection[1]);
          userEvent.click(
            screen.getByRole("button", { name: "Save and continue" })
          );

          await waitFor(() => {
            expect(update).toHaveBeenCalledWith(claim_id, {
              residential_address: unformattedAddress,
              has_mailing_address: true,
              mailing_address: unformattedAddress,
            });
          });
        });

        it("removes suggestions when user clicks Edit address", async () => {
          await screen.findByTestId("residential-address-error");
          await screen.findByTestId("mailing-address-error");

          const selection = screen.getAllByText("Edit address");

          userEvent.click(selection[0]);
          userEvent.click(selection[1]);

          await waitFor(() => {
            expect(
              screen.queryByTestId("residential-address-error")
            ).not.toBeInTheDocument();
            expect(
              screen.queryByTestId("mailing-address-error")
            ).not.toBeInTheDocument();
          });
        });
      });
    });
  });
});
