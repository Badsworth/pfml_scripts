import Claim, {
  PaymentAccountType,
  PaymentPreferenceMethod,
} from "../../models/Claim";
import { cloneDeep, get, pick, set } from "lodash";
import ConditionalContent from "../../components/ConditionalContent";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.payment_preferences[0].payment_method",
  "claim.payment_preferences[0].account_details.account_number",
  "claim.payment_preferences[0].account_details.account_type",
  "claim.payment_preferences[0].account_details.routing_number",
];

export const PaymentMethod = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, clearField } = useFormState(
    pick(props, fields).claim
  );

  const account_type = get(
    formState,
    "payment_preferences[0].account_details.account_type"
  );
  const payment_method = get(
    formState,
    "payment_preferences[0].payment_method"
  );

  const handleSave = async () => {
    /**
     * We need to include the payment_preference_id if one exists, so the
     * API merges changes, rather than creates a different payment preference.
     * We access this ID from the `claim` prop, rather than including it
     * as part of our initial form state, because there are scenarios where a
     * payment preference can be created and not reflected back in our form state,
     * such as when the user has validation issues when initially submitting
     * the page.
     */
    const paymentPreferenceIdPath =
      "payment_preferences[0].payment_preference_id";
    const payment_preference_id = get(claim, paymentPreferenceIdPath);
    const requestData = cloneDeep(formState);

    if (payment_preference_id) {
      set(requestData, paymentPreferenceIdPath, payment_preference_id);
    }

    await appLogic.claims.update(claim.application_id, requestData);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsPaymentMethod.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("payment_preferences[0].payment_method")}
        choices={[
          {
            checked: payment_method === PaymentPreferenceMethod.ach,
            label: t("pages.claimsPaymentMethod.choiceAch"),
            hint: t("pages.claimsPaymentMethod.choiceHintAch"),
            value: PaymentPreferenceMethod.ach,
          },
          {
            checked: payment_method === PaymentPreferenceMethod.check,
            label: t("pages.claimsPaymentMethod.choiceCheck"),
            hint: t("pages.claimsPaymentMethod.choiceHintCheck"),
            value: PaymentPreferenceMethod.check,
          },
        ]}
        label={t("pages.claimsPaymentMethod.sectionLabel")}
        type="radio"
        hint={t("pages.claimsPaymentMethod.sectionLabelHint")}
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "payment_preferences[0].account_details.account_number",
          "payment_preferences[0].account_details.account_type",
          "payment_preferences[0].account_details.routing_number",
        ]}
        getField={getField}
        updateFields={updateFields}
        clearField={clearField}
        visible={payment_method === PaymentPreferenceMethod.ach}
      >
        <Fieldset>
          <FormLabel component="legend">
            {t("pages.claimsPaymentMethod.achSectionLabel")}
          </FormLabel>
          <Lead>{t("pages.claimsPaymentMethod.achLead")}</Lead>

          <InputText
            {...getFunctionalInputProps(
              "payment_preferences[0].account_details.routing_number"
            )}
            label={t("pages.claimsPaymentMethod.routingNumberLabel")}
            hint={t("pages.claimsPaymentMethod.routingNumberHint")}
            inputMode="numeric"
            smallLabel
            width="medium"
            pii
          />

          <InputText
            {...getFunctionalInputProps(
              "payment_preferences[0].account_details.account_number"
            )}
            label={t("pages.claimsPaymentMethod.accountNumberLabel")}
            inputMode="numeric"
            smallLabel
            pii
          />

          <InputChoiceGroup
            {...getFunctionalInputProps(
              "payment_preferences[0].account_details.account_type"
            )}
            choices={[
              {
                checked: account_type === PaymentAccountType.checking,
                label: t("pages.claimsPaymentMethod.achTypeChecking"),
                value: PaymentAccountType.checking,
              },
              {
                checked: account_type === PaymentAccountType.savings,
                label: t("pages.claimsPaymentMethod.achTypeSavings"),
                value: PaymentAccountType.savings,
              },
            ]}
            label={t("pages.claimsPaymentMethod.achTypeLabel")}
            type="radio"
            smallLabel
          />
        </Fieldset>
      </ConditionalContent>
    </QuestionPage>
  );
};

PaymentMethod.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(PaymentMethod);
