import React, { useEffect } from "react";
import { pick, uniqueId } from "lodash";
import useAddressFormatter, {
  AddressFormatter,
} from "../../hooks/useAddressFormatter";
import AddressModel from "../../models/Address";
import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import Button from "../../components/Button";
import ConditionalContent from "../../components/ConditionalContent";
import FieldsetAddress from "../../components/FieldsetAddress";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import { isFeatureEnabled } from "../../services/featureFlags";
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
    if (isFeatureEnabled("claimantValidateAddress")) {
      formData.residential_address = await residentialAddressFormatter.format();

      if (formData.has_mailing_address) {
        formData.mailing_address = await mailingAddressFormatter.format();
        if (!formData.mailing_address) return;
      }

      if (!formData.residential_address) return;
    }

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
              data-testid="residential-address-error"
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
                data-testid="mailing-address-error"
              />
            )
          }
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(Address);

interface AddressFormattingErrorProps {
  addressFormatter: AddressFormatter;
  "data-testid"?: string;
}

const AddressFormattingError = (props: AddressFormattingErrorProps) => {
  const { addressFormatter, "data-testid": dataTestId } = props;
  const { t } = useTranslation();

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    addressFormatter.selectSuggestionAddressKey(event.target.value);
  };

  if (addressFormatter.suggestions.length === 0) {
    return (
      <div className="border-left-05 padding-left-2" data-testid={dataTestId}>
        <InputChoiceGroup
          smallLabel
          label={t("pages.claimsAddress.validationSuggestionNoMatchLabel")}
          hint={t("pages.claimsAddress.validationSuggestionNoMatchHint")}
          type="radio"
          name={uniqueId("address-formatting-error")}
          onChange={handleChange}
          choices={[
            {
              checked: addressFormatter.selectedAddressKey === "none",
              label: t(
                "pages.claimsAddress.validationSuggestionNoMatchRadioLabel"
              ),
              hint: addressFormatter.address.toString(),
              value: "none",
            },
          ]}
        />
        <Button onClick={addressFormatter.reset} variation="unstyled">
          {t("pages.claimsAddress.validationSuggestionEditAddressLink")}
        </Button>
      </div>
    );
  }

  return (
    <div className="border-left-05 padding-left-2" data-testid={dataTestId}>
      <InputChoiceGroup
        smallLabel
        label={t("pages.claimsAddress.validationSuggestionLabel")}
        hint={t("pages.claimsAddress.validationSuggestionHint")}
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
        hint={t("pages.claimsAddress.validationSuggestionEnteredHint")}
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
        {t("pages.claimsAddress.validationSuggestionEditAddressLink")}
      </Button>
    </div>
  );
};
