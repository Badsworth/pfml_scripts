import Address from "../models/Address";
import { AddressValidationError } from "../errors";

const authToken: string = process.env.experianApiKey || "";

interface ExperianSuggestion {
  global_address_key: string;
  text: string;
  matched: number[][];
  format: string;
}

interface ExperianSearchResult {
  result: {
    more_results_available: boolean;
    confidence:
      | "Verified match"
      | "Multiple matches"
      | "No matches"
      | "Insufficient search terms";
    suggestions: ExperianSuggestion[];
  };
}

interface ExperianFormatResult {
  result: {
    global_address_key: string;
    confidence:
      | "Verified match"
      | "Multiple matches"
      | "No matches"
      | "Insufficient search terms";
    address: {
      address_line_1: string;
      address_line_2: string;
      address_line_3: string;
      locality: string;
      region: string;
      postal_code: string;
      country: string;
    };
  };
}

export interface AddressSuggestion {
  addressKey: string;
  address: string;
}

export const findAddress = async (
  address: Address
): Promise<AddressSuggestion> => {
  const experianResult = await search(address.toString());

  if (experianResult.result.confidence !== "Verified match") {
    const suggestions = experianResult.result.suggestions.map(
      (suggestion: ExperianSuggestion): AddressSuggestion => ({
        addressKey: suggestion.global_address_key,
        address: suggestion.text,
      })
    );
    throw new AddressValidationError(suggestions);
  }

  return {
    addressKey: experianResult.result.suggestions[0].global_address_key,
    address: experianResult.result.suggestions[0].text,
  };
};

export const formatAddress = async (addressKey: string): Promise<Address> => {
  const experianResult = await format(addressKey);

  const address = experianResult.result.address;

  return new Address({
    line_1: address.address_line_1,
    line_2: address.address_line_2,
    state: address.region,
    city: address.locality,
    zip: address.postal_code?.split("-")[0],
  });
};

const search = async (address: string): Promise<ExperianSearchResult> => {
  const requestBody = {
    country_iso: "USA",
    components: {
      unspecified: [address],
    },
  };

  const response = await fetch(
    "https://api.experianaperture.io/address/search/v1",
    {
      method: "POST",
      headers: {
        "Auth-Token": authToken,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(requestBody),
    }
  );

  const experianResult: ExperianSearchResult = await response.json();

  return experianResult;
};

const format = async (addressKey: string): Promise<ExperianFormatResult> => {
  const response = await fetch(
    `https://api.experianaperture.io/address/format/v1/${addressKey}`,
    {
      method: "GET",
      headers: {
        "Auth-Token": authToken,
        Accept: "application/json",
        "Add-Components": "false",
        "Add-Metadata": "false",
      },
    }
  );

  const experianResult: ExperianFormatResult = await response.json();

  return experianResult;
};
