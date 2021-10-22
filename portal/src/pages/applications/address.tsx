import {
  AddressSuggestion,
  format,
  search,
  searchAddress,
} from "../../services/experian";
import React, { useEffect, useState } from "react";
import { keyBy, pick } from "lodash";
import AddressModel from "../../models/Address";
import Autocomplete from "accessible-autocomplete/react";
import BenefitsApplication from "../../models/BenefitsApplication";
import ConditionalContent from "../../components/ConditionalContent";
import FieldsetAddress from "../../components/FieldsetAddress";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import Modal from "../../components/Modal";
import QuestionPage from "../../components/QuestionPage";
import Spinner from "../../components/Spinner";
import ThrottledButton from "../../components/ThrottledButton";

import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
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
  "claim.mailing_address.state",
  "claim.mailing_address.zip",
];

interface AddressProps {
  claim?: BenefitsApplication;
  appLogic: any;
  query?: {
    claim_id?: string;
  };
}

export const Address = (props: AddressProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );

  const [addressSuggestions, setAddressSuggestions] = useState<
    AddressSuggestion[]
  >([]);
  const [isModalVisible, setIsModalVisible] = useState<boolean>(false);
  const [choices, setChoices] = useState<Record<string, AddressSuggestion>>({});

  const { has_mailing_address } = formState;

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

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const residentialAddressProps = getFunctionalInputProps(
    "residential_address"
  );
  if (!residentialAddressProps.value) {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    residentialAddressProps.value = new AddressModel();
  }

  const mailingAddressProps = getFunctionalInputProps("mailing_address");
  if (!mailingAddressProps.value) {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    mailingAddressProps.value = new AddressModel();
  }

  const handleValidateClick = async () => {
    const suggestions = await searchAddress(
      new AddressModel(residentialAddressProps.value)
    );
    setAddressSuggestions(suggestions);
    setIsModalVisible(true);
  };

  const handleAddressSuggestionClick = useThrottledHandler<string>(
    async (addressKey) => {
      const validatedAddress = await format(addressKey);

      updateFields({ residential_address: validatedAddress });
      setAddressSuggestions([]);
      setIsModalVisible(false);
    }
  );

  const handleAutocompleteChange = useThrottledHandler(
    async (
      searchString: string,
      populateResults: (results: string[]) => void
    ) => {
      const suggestions = await search(searchString);
      const results = suggestions.map((choice) => choice.address);
      setChoices(keyBy(suggestions, (suggestion) => suggestion.address));
      populateResults(results);
    }
  );

  const handleConfirm = async (confirmed: string) => {
    const validatedAddress = await format(choices[confirmed].addressKey);

    updateFields({ mailing_address: validatedAddress });
  };

  return (
    <React.Fragment>
      <QuestionPage title={t("pages.claimsAddress.title")} onSave={handleSave}>
        <FieldsetAddress
          appErrors={appLogic.appErrors}
          label={t("pages.claimsAddress.sectionLabel")}
          hint={t("pages.claimsAddress.hint")}
          {...residentialAddressProps}
        />
        <ThrottledButton onClick={handleValidateClick}>
          Validate
        </ThrottledButton>
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
          <div className="usa-form-group">
            <FormLabel>Residential address</FormLabel>
            <Autocomplete
              defaultValue={
                new AddressModel(mailingAddressProps.value).toString
              }
              source={handleAutocompleteChange}
              onConfirm={handleConfirm}
              confirmOnBlur={false}
            />
          </div>
        </ConditionalContent>
      </QuestionPage>
      <Modal
        isVisible={isModalVisible}
        headingText="Do any of these addresses look right?"
        onCloseButtonClick={() => setIsModalVisible(false)}
      >
        <ul>
          {addressSuggestions.map((suggestion: AddressSuggestion) => (
            <li
              key={suggestion.addressKey}
              className="hover:bg-base-lightest cursor-pointer"
              onKeyDown={() => null}
              role="option"
              onClick={() =>
                handleAddressSuggestionClick(suggestion.addressKey)
              }
            >
              {suggestion.address}
            </li>
          ))}
        </ul>
        {handleAddressSuggestionClick.isThrottled && (
          <Spinner aria-valuetext="Loading..." />
        )}
      </Modal>
    </React.Fragment>
  );
};

export default withBenefitsApplication(Address);
