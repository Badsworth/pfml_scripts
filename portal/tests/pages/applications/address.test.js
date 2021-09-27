import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import Address from "../../../src/pages/applications/address";
import AddressModel from "../../../src/models/Address";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
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
});
