import AddressModel from "../models/Address";
import { compact } from "lodash";

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

export const searchAddress = async (
  address: AddressModel
): Promise<AddressSuggestion[]> => {
  return await search(address.toString);
};

export const search = async (address: string): Promise<AddressSuggestion[]> => {
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
        "Auth-Token": "",
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(requestBody),
    }
  );

  const experianResult: ExperianSearchResult = await response.json();

  return experianResult.result.suggestions.map(
    (suggestion: ExperianSuggestion): AddressSuggestion => ({
      addressKey: suggestion.global_address_key,
      address: suggestion.text,
    })
  );
};

export const format = async (addressKey: string): Promise<AddressModel> => {
  const response = await fetch(
    `https://api.experianaperture.io/address/format/v1/${addressKey}`,
    {
      method: "GET",
      headers: {
        "Auth-Token": "",
        Accept: "application/json",
        "Add-Components": "false",
        "Add-Metadata": "false",
      },
    }
  );

  const experianResult: ExperianFormatResult = await response.json();
  const address = experianResult.result.address;

  return new AddressModel({
    line_1: address.address_line_1,
    line_2: address.address_line_2,
    state: address.region,
    city: address.locality,
    zip: address.postal_code?.split("-")[0],
  });
};
