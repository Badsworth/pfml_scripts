import {
  AddressSuggestion,
  findAddress,
  formatAddress,
} from "../services/addressValidator";
import Address from "../models/Address";
import { AddressValidationError } from "../errors";
import { useState } from "react";

export interface AddressFormatter {
  address: Address;
  selectedAddressKey?: string | null;
  selectSuggestionAddressKey: (suggestionAddressKey: string) => void;
  couldBeFormatted?: boolean | null;
  format: () => Promise<Address | undefined>;
  reset: () => void;
  suggestions: AddressSuggestion[];
}

/**
 * Manage state and actions around formatting an Address into a valid postal address. If an address can be formatted multiple ways,
 * it provides a list of AddressSuggestions that the user can select from. If no valid address
 * is found, a user can skip formatting.
 * @param address Address to be formatted
 * @param onError Error handler
 * @returns
 */
const useAddressFormatter = (
  address: Address,
  onError: (error: unknown) => void
): AddressFormatter => {
  const [couldBeFormatted, setCouldBeFormatted] = useState<boolean | null>();
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [selectedAddressKey, setSelectedAddressKey] = useState<
    AddressSuggestion["addressKey"] | "none" | null
  >();

  const shouldSkipFormatting = selectedAddressKey === "none";
  const addressIsMasked = address.line_1 === "*******";

  const format = async (): Promise<Address | undefined> => {
    if (shouldSkipFormatting || addressIsMasked) {
      setCouldBeFormatted(true);
      return address;
    }

    if (selectedAddressKey) {
      try {
        setSelectedAddressKey(null);
        setSuggestions([]);
        setCouldBeFormatted(true);
        return await formatAddress(selectedAddressKey);
      } catch (error: unknown) {
        onError(error);
        return;
      }
    }

    try {
      const addressSuggestion = await findAddress(address);
      setSuggestions([]);
      setCouldBeFormatted(true);
      return await formatAddress(addressSuggestion.addressKey);
    } catch (error: AddressValidationError | unknown) {
      if (error instanceof AddressValidationError) {
        setSuggestions(error.suggestions);
        setCouldBeFormatted(false);
      }
      onError(error);
    }
  };

  const reset = () => {
    setSuggestions([]);
    setCouldBeFormatted(null);
    setSelectedAddressKey(null);
  };

  const selectSuggestionAddressKey = (suggestionAddressKey: string) => {
    setSelectedAddressKey(suggestionAddressKey);
  };

  return {
    address,
    selectedAddressKey,
    selectSuggestionAddressKey,
    couldBeFormatted,
    format,
    reset,
    suggestions,
  };
};

export default useAddressFormatter;
