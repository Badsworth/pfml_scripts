import { AddressValidationError, ExperianApiError } from "../../src/errors";
import {
  findAddress,
  formatAddress,
} from "../../src/services/addressValidator";
import Address from "../../src/models/Address";
import { rest } from "msw";
import { setupServer } from "msw/node";

const server = setupServer();

beforeAll(() => {
  server.listen();
});

afterAll(() => {
  server.close();
});

afterEach(() => server.resetHandlers());
describe(findAddress, () => {
  it("returns AddressSuggestion when validation service returns a verified match", async () => {
    server.use(
      rest.post(
        "https://api.experianaperture.io/address/search/v1",
        (req, res, ctx) => {
          return res(
            ctx.json({
              result: {
                more_results_available: false,
                confidence: "Verified match",
                suggestions: [
                  {
                    global_address_key: "mockaddresskeyapt1",
                    matched: [],
                    text: "54321 Mock Address Apt 1 Washington, DC 20005",
                    format:
                      "https://api.experianaperture.io/address/format/v1/mockaddresskeyapt1",
                  },
                ],
              },
            })
          );
        }
      )
    );

    const result = await findAddress(new Address());

    expect(result).toEqual({
      addressKey: "mockaddresskeyapt1",
      address: "54321 Mock Address Apt 1 Washington, DC 20005",
    });
  });

  it("throws AddressValidationError when validation service returns more than 1 result", async () => {
    server.use(
      rest.post(
        "https://api.experianaperture.io/address/search/v1",
        (req, res, ctx) => {
          return res(
            ctx.json({
              result: {
                more_results_available: true,
                confidence: "Multiple matches",
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
            })
          );
        }
      )
    );

    expect.assertions(2);
    try {
      await findAddress(new Address());
    } catch (e) {
      expect(e).toBeInstanceOf(AddressValidationError);
      expect(e.suggestions).toMatchInlineSnapshot(`
Array [
  Object {
    "address": "54321 Mock Address Apt 1 Washington, DC 20005",
    "addressKey": "mockaddresskeyapt1",
  },
  Object {
    "address": "54321 Mock Address Apt 2 Washington, DC 20005",
    "addressKey": "mockaddresskeyapt2",
  },
]
`);
    }
  });

  it("throws AddressValidationError when validation service returns no matches", async () => {
    server.use(
      rest.post(
        "https://api.experianaperture.io/address/search/v1",
        (req, res, ctx) => {
          return res(
            ctx.json({
              result: {
                more_results_available: true,
                confidence: "No matches",
                suggestions: [],
              },
            })
          );
        }
      )
    );
    expect.assertions(2);
    try {
      await findAddress(new Address());
    } catch (e) {
      expect(e).toBeInstanceOf(AddressValidationError);
      expect(e.suggestions).toEqual([]);
    }
  });

  it("throws ExperianApiError when validation service returns unauthorized status", async () => {
    server.use(
      rest.post(
        "https://api.experianaperture.io/address/search/v1",
        (req, res, ctx) => {
          return res(ctx.status(401));
        }
      )
    );

    expect.assertions(1);
    try {
      await findAddress(new Address());
    } catch (e) {
      expect(e).toBeInstanceOf(ExperianApiError);
    }
  });

  it("throws ExperianApiError when validation service fails", async () => {
    server.use(
      rest.post(
        "https://api.experianaperture.io/address/search/v1",
        (req, res, ctx) => {
          return res.networkError();
        }
      )
    );
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    expect.assertions(2);
    try {
      await findAddress(new Address());
    } catch (e) {
      expect(console.error).toHaveBeenCalled();
      expect(e).toBeInstanceOf(ExperianApiError);
    }
  });
});

describe(formatAddress, () => {
  const formattedAddress = new Address({
    line_1: "FORMATTED address 1",
    line_2: "Line 2",
    city: "City",
    state: "State",
    zip: "20005",
  });

  it("returns formattedAddress when validation service is successful", async () => {
    server.use(
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

    expect(await formatAddress("mockaddresskey")).toEqual(formattedAddress);
  });

  it("throws ExperianApiError when validation service returns unauthorized", async () => {
    server.use(
      rest.get(
        "https://api.experianaperture.io/address/format/v1/:addressKey",
        (req, res, ctx) => {
          return res(ctx.status(401));
        }
      )
    );

    expect.assertions(1);
    try {
      await formatAddress("mockaddresskey");
    } catch (e) {
      expect(e).toBeInstanceOf(ExperianApiError);
    }
  });

  it("throws ExperianApiError when validation service fails", async () => {
    server.use(
      rest.get(
        "https://api.experianaperture.io/address/format/v1/:addressKey",
        (req, res, ctx) => {
          return res.networkError();
        }
      )
    );
    jest.spyOn(console, "error").mockImplementation(jest.fn());
    expect.assertions(2);
    try {
      await formatAddress("mockaddresskey");
    } catch (e) {
      expect(console.error).toHaveBeenCalled();
      expect(e).toBeInstanceOf(ExperianApiError);
    }
  });
});
