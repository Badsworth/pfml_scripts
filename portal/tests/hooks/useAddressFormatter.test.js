import Address from "../../src/models/Address";
import { act } from "@testing-library/react";
import { renderHook } from "@testing-library/react-hooks";
import { rest } from "msw";
import { setupServer } from "msw/node";
import useAddressFormatter from "../../src/hooks/useAddressFormatter";

const formattedAddress = new Address({
  line_1: "FORMATTED address 1",
  line_2: "Line 2",
  city: "City",
  state: "State",
  zip: "20005",
});

const suggestions = [
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
];

const mockFormatRequest = (req, res, ctx) => {
  if (req.params.addressKey === "address that fails at format request") {
    throw new Error();
  }
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
};

const mockSearchRequest = (req, res, ctx) => {
  const address = req.body.components.unspecified[0];

  if (address.includes("address with multiple matches")) {
    return res(
      ctx.json({
        result: {
          more_results_available: false,
          confidence: "Multiple matches",
          suggestions,
        },
      })
    );
  }

  if (address.includes("address with no matches")) {
    return res(
      ctx.json({
        result: {
          more_results_available: false,
          confidence: "No matches",
          suggestions: [],
        },
      })
    );
  }

  if (address.includes("address that fails at format request")) {
    return res(
      ctx.json({
        result: {
          more_results_available: false,
          confidence: "Verified match",
          suggestions: [
            {
              ...suggestions[0],
              global_address_key: "address that fails at format request",
            },
          ],
        },
      })
    );
  }

  return res(
    ctx.json({
      result: {
        more_results_available: false,
        confidence: "Verified match",
        suggestions: [suggestions[0]],
      },
    })
  );
};

const server = setupServer(
  rest.get(
    "https://api.experianaperture.io/address/format/v1/:addressKey",
    mockFormatRequest
  ),
  rest.post(
    "https://api.experianaperture.io/address/search/v1",
    mockSearchRequest
  )
);

beforeAll(() => {
  server.listen();
});

afterAll(() => {
  server.close();
});

afterEach(() => server.resetHandlers());

describe(useAddressFormatter, () => {
  const handleError = jest.fn();

  describe("#selectSuggestionAddressKey", () => {
    it("sets the selectedAddressKey", () => {
      const address = new Address({
        line_1: "54321 Mock Address",
        line_2: "",
        city: "Washington",
        state: "DC",
      });
      const { result } = renderHook(() =>
        useAddressFormatter(address, handleError)
      );
      act(() => result.current.selectSuggestionAddressKey("addresskey"));

      expect(result.current.selectedAddressKey).toEqual("addresskey");
    });
  });

  describe("#format", () => {
    it("returns unformatted address when address is masked", async () => {
      const address = new Address({
        line_1: "*******",
      });
      const { result } = renderHook(
        () => useAddressFormatter(address),
        handleError
      );

      let formatResult;
      await act(async () => {
        formatResult = await result.current.format();
      });
      expect(formatResult).toEqual(address);
    });

    it("returns unformatted address when selectedAddressKey is none", async () => {
      const address = new Address({
        line_1: "54321 Mock Address",
        line_2: "",
        city: "Washington",
        state: "DC",
      });
      const { result } = renderHook(() =>
        useAddressFormatter(address, handleError)
      );

      act(() => result.current.selectSuggestionAddressKey("none"));
      let formatResult;
      await act(async () => {
        formatResult = await result.current.format();
      });
      expect(formatResult).toEqual(address);
    });

    describe("when selectedAddressKey is set and does not equal none", () => {
      let result;

      beforeEach(() => {
        const address = new Address({
          line_1: "54321 Mock Address",
          line_2: "",
          city: "Washington",
          state: "DC",
        });
        ({ result } = renderHook(() =>
          useAddressFormatter(address, handleError)
        ));

        act(() => result.current.selectSuggestionAddressKey("addresskey"));
      });

      it("returns formatted address", async () => {
        let formatResult;
        await act(async () => {
          formatResult = await result.current.format();
        });
        expect(formatResult).toEqual(formattedAddress);
      });

      it("sets selected key to null", async () => {
        await act(async () => await result.current.format());
        expect(result.current.selectedAddressKey).toEqual(null);
      });

      it("sets couldBeFormatted to true", async () => {
        await act(async () => await result.current.format());
        expect(result.current.couldBeFormatted).toEqual(true);
      });

      it("set suggestions to empty array", async () => {
        await act(async () => await result.current.format());
        expect(result.current.suggestions).toEqual([]);
      });
    });

    it("calls error handler when selectedAddressKey is set but address can't be formatted", async () => {
      const address = new Address({
        line_1: "54321 Mock Address",
        line_2: "",
        city: "Washington",
        state: "DC",
      });
      const { result } = renderHook(() =>
        useAddressFormatter(address, handleError)
      );

      act(() =>
        result.current.selectSuggestionAddressKey(
          "address that fails at format request"
        )
      );

      expect(await result.current.format()).toEqual(undefined);
      expect(handleError).toHaveBeenCalled();
    });

    describe("when address is successfully formatted", () => {
      let result;

      beforeEach(() => {
        const address = new Address({
          line_1: "54321 Mock Address",
          line_2: "",
          city: "Washington",
          state: "DC",
        });
        ({ result } = renderHook(() =>
          useAddressFormatter(address, handleError)
        ));
      });

      it("returns formatted address", async () => {
        let formatResult;
        await act(async () => {
          formatResult = await result.current.format();
        });
        expect(formatResult).toEqual(formattedAddress);
      });

      it("sets suggestions to empty array", async () => {
        await act(async () => await result.current.format());
        expect(result.current.suggestions).toEqual([]);
      });

      it("sets couldBeFormatted to true", async () => {
        await act(async () => await result.current.format());
        expect(result.current.couldBeFormatted).toEqual(true);
      });
    });

    describe("when address can be formatted multiple ways", () => {
      let result;

      beforeEach(() => {
        const address = new Address({
          line_1: "address with multiple matches",
          line_2: "",
          city: "Washington",
          state: "DC",
        });
        ({ result } = renderHook(() =>
          useAddressFormatter(address, handleError)
        ));
      });

      it("returns undefined", async () => {
        let formatResult;
        await act(async () => {
          formatResult = await result.current.format();
        });
        expect(formatResult).toEqual(undefined);
      });

      it("sets suggestions", async () => {
        await act(async () => await result.current.format());
        expect(result.current.suggestions).toEqual([
          {
            address: "54321 Mock Address Apt 1 Washington, DC 20005",
            addressKey: "mockaddresskeyapt1",
          },
          {
            address: "54321 Mock Address Apt 2 Washington, DC 20005",
            addressKey: "mockaddresskeyapt2",
          },
        ]);
      });

      it("sets couldBeFormatted to false", async () => {
        await act(async () => await result.current.format());
        expect(result.current.couldBeFormatted).toEqual(false);
      });

      it("calls error handler", async () => {
        await act(async () => await result.current.format());
        expect(handleError).toHaveBeenCalled();
      });
    });

    it("calls error handler when service requests fail", async () => {
      const address = new Address({
        line_1: "address that fails at format call",
        line_2: "",
        city: "Washington",
        state: "DC",
      });
      const { result } = renderHook(() =>
        useAddressFormatter(address, handleError)
      );

      expect(await result.current.format()).toEqual(undefined);
      expect(handleError).toHaveBeenCalled();
    });
  });

  describe("#reset", () => {
    it("resets all states", async () => {
      const address = new Address({
        line_1: "address with multiple matches",
        line_2: "",
        city: "Washington",
        state: "DC",
      });
      const { result } = renderHook(() =>
        useAddressFormatter(address, handleError)
      );

      await act(async () => await result.current.format());

      act(() => result.current.reset());
      expect(result.current.suggestions).toEqual([]);
      expect(result.current.couldBeFormatted).toEqual(null);
      expect(result.current.selectedAddressKey).toEqual(null);
    });
  });
});
