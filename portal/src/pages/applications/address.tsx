import {
  AddressSuggestion,
  findAddress,
  formatAddress,
} from "../../services/addressValidator";
import React, { useEffect, useState } from "react";
import { pick, uniqueId } from "lodash";
import AddressModel from "../../models/Address";
import { AddressValidationError } from "../../errors";
import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import Button from "../../components/Button";
import ConditionalContent from "../../components/ConditionalContent";
import FieldsetAddress from "../../components/FieldsetAddress";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.has_mailing_address",
  "claim.residential_address.line_1",
  "claim.residential_address.line_2",
  "claim.residential_address.city",
  "claim.residential_address.state",
  "claim.residential_address.zip",
  // Include `mailing_address` so validation error shows for completely empty mailing address.
  // We don't need this for `residential_address` since that defaults to a blank object, rather than null.
  "claim.mailing_address",
  "claim.mailing_address.line_1",
  "claim.mailing_address.line_2",
  "claim.mailing_address.city",
  "claim.mailing_address.sate",
  "claim.mailing_address.zip",
];

interface AddressProps {
  claim: BenefitsApplication;
  appLogic: AppLogic;
  query: {
    claim_id?: string;
  };
}

interface AddressFormatter {
  address: AddressModel;
  selectedAddressKey?: string | null;
  selectSuggestionAddressKey: (suggestionAddressKey: string) => void;
  couldBeFormatted?: boolean | null;
  format: () => Promise<AddressModel | undefined>;
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
  address: AddressModel,
  onError: (error: unknown) => void
): AddressFormatter => {
  const [couldBeFormatted, setCouldBeFormatted] = useState<boolean | null>();
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [addressKey, setAddressKey] = useState<"none" | string | null>();

  const shouldSkipFormatting = addressKey === "none";
  const addressIsMasked = address.line_1 === "*******";

  const format = async (): Promise<AddressModel | undefined> => {
    if (shouldSkipFormatting || addressIsMasked) {
      setCouldBeFormatted(true);
      return address;
    }

    if (addressKey) {
      try {
        setAddressKey(null);
        setSuggestions([]);
        setCouldBeFormatted(true);
        return await formatAddress(addressKey);
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
    setAddressKey(null);
  };

  const selectSuggestionAddressKey = (suggestionAddressKey: string) => {
    setAddressKey(suggestionAddressKey);
  };

  return {
    address,
    selectedAddressKey: addressKey,
    selectSuggestionAddressKey,
    couldBeFormatted,
    format,
    reset,
    suggestions,
  };
};

interface AddressFormattingErrorProps {
  addressFormatter: AddressFormatter;
}

const AddressFormattingError = (props: AddressFormattingErrorProps) => {
  const { addressFormatter } = props;

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    addressFormatter.selectSuggestionAddressKey(event.target.value);
  };

  if (addressFormatter.suggestions.length === 0) {
    return (
      <div className="border-left-05 padding-left-2">
        <InputChoiceGroup
          smallLabel
          label="Verify address"
          hint={"We could not verify your address as entered"}
          type="radio"
          name={uniqueId("address-formatting-error")}
          onChange={handleChange}
          choices={[
            {
              checked: addressFormatter.selectedAddressKey === "none",
              label: "Use address as entered:",
              hint: addressFormatter.address.toString(),
              value: "none",
            },
          ]}
        />
        <Button onClick={addressFormatter.reset} variation="unstyled">
          Edit address
        </Button>
      </div>
    );
  }

  return (
    <div className="border-left-05 padding-left-2">
      <InputChoiceGroup
        smallLabel
        label="Verify your address"
        hint="Suggested:"
        type="radio"
        name={uniqueId("address-formatting-error")}
        onChange={handleChange}
        choices={addressFormatter.suggestions.map((suggestion) => ({
          checked:
            addressFormatter.selectedAddressKey === suggestion.addressKey,
          label: suggestion.address,
          value: suggestion.addressKey,
        }))}
      />
      <InputChoiceGroup
        smallLabel
        label=""
        hint="Entered:"
        type="radio"
        name={uniqueId("address-formatting-error")}
        onChange={handleChange}
        choices={[
          {
            checked: addressFormatter.selectedAddressKey === "none",
            label: addressFormatter.address.toString(),
            value: "none",
          },
        ]}
      />
      <Button onClick={addressFormatter.reset} variation="unstyled">
        Edit address
      </Button>
    </div>
  );
};

export const Address = (props: AddressProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );

  const { has_mailing_address } = formState;

  const residentialAddressFormatter = useAddressFormatter(
    new AddressModel(formState.residential_address),
    appLogic.catchError
  );
  const mailingAddressFormatter = useAddressFormatter(
    new AddressModel(formState.mailing_address),
    appLogic.catchError
  );

  /**
   * When user indicates they have a mailing address,
   * add a blank mailing address so validations are ran against it
   */
  useEffect(() => {
    const existingMailingAddress = formState.mailing_address;
    if (formState.has_mailing_address && !existingMailingAddress) {
      updateFields({ mailing_address: {} });
    }
  }, [formState, updateFields]);

  const handleSave = async () => {
    const formData = { ...formState };
    formData.residential_address = await residentialAddressFormatter.format();

    if (has_mailing_address) {
      formData.mailing_address = await mailingAddressFormatter.format();
      if (!formData.mailing_address) return;
    }

    if (!formData.residential_address) return;

    await appLogic.benefitsApplications.update(claim.application_id, formData);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const residentialAddressProps = getFunctionalInputProps(
    "residential_address"
  );
  if (!residentialAddressProps.value) {
    residentialAddressProps.value = new AddressModel({});
  }

  const mailingAddressProps = getFunctionalInputProps("mailing_address");
  if (!mailingAddressProps.value) {
    mailingAddressProps.value = new AddressModel({});
  }

  return (
    <QuestionPage title={t("pages.claimsAddress.title")} onSave={handleSave}>
      <FieldsetAddress
        appErrors={appLogic.appErrors}
        label={t("pages.claimsAddress.sectionLabel")}
        hint={t("pages.claimsAddress.hint")}
        {...residentialAddressProps}
        errorMsg={
          residentialAddressFormatter.couldBeFormatted === false && (
            <AddressFormattingError
              addressFormatter={residentialAddressFormatter}
            />
          )
        }
      />
      <InputChoiceGroup
        {...getFunctionalInputProps("has_mailing_address")}
        choices={[
          {
            checked: has_mailing_address === false,
            label: t("pages.claimsAddress.choiceYes"),
            value: "false",
          },
          {
            checked: has_mailing_address === true,
            label: t("pages.claimsAddress.choiceNo"),
            value: "true",
          },
        ]}
        label={t("pages.claimsAddress.hasMailingAddressLabel")}
        hint={t("pages.claimsAddress.hasMailingAddressHint")}
        type="radio"
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={["mailing_address"]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
        visible={has_mailing_address}
      >
        <FieldsetAddress
          appErrors={appLogic.appErrors}
          label={t("pages.claimsAddress.mailingAddressLabel")}
          hint={t("pages.claimsAddress.mailingAddressHint")}
          addressType="mailing"
          {...mailingAddressProps}
          errorMsg={
            mailingAddressFormatter.couldBeFormatted === false && (
              <AddressFormattingError
                addressFormatter={mailingAddressFormatter}
              />
            )
          }
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(Address);
