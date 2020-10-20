import AddressModel from "../../models/Address";
import Claim from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import FieldsetAddress from "../../components/FieldsetAddress";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

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

export const Address = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );

  const { has_mailing_address } = formState;

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const residentialAddressProps = getFunctionalInputProps(
    "residential_address"
  );
  if (!residentialAddressProps.value) {
    residentialAddressProps.value = new AddressModel();
  }

  const mailingAddressProps = getFunctionalInputProps("mailing_address");
  if (!mailingAddressProps.value) {
    mailingAddressProps.value = new AddressModel();
  }

  return (
    <QuestionPage title={t("pages.claimsAddress.title")} onSave={handleSave}>
      <FieldsetAddress
        appErrors={appLogic.appErrors}
        label={t("pages.claimsAddress.sectionLabel")}
        hint={t("pages.claimsAddress.hint")}
        {...residentialAddressProps}
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
          {...mailingAddressProps}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

Address.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Address);
