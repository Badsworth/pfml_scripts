import Claim, { PaymentPreferenceMethod } from "../../models/Claim";
import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import pick from "lodash/pick";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "claim.temp.payment_preferences[0].payment_method",
  "claim.temp.payment_preferences[0].account_details.account_number",
  "claim.temp.payment_preferences[0].account_details.routing_number",
];

export const PaymentMethod = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const paymentPreference = get(formState, "temp.payment_preferences[0]");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

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
        {...getFunctionalInputProps(
          "temp.payment_preferences[0].payment_method"
        )}
        choices={[
          {
            checked:
              paymentPreference.payment_method === PaymentPreferenceMethod.ach,
            label: t("pages.claimsPaymentMethod.choiceAch"),
            hint: t("pages.claimsPaymentMethod.choiceHintAch"),
            value: PaymentPreferenceMethod.ach,
          },
          {
            checked:
              paymentPreference.payment_method ===
              PaymentPreferenceMethod.debit,
            label: t("pages.claimsPaymentMethod.choiceDebit"),
            hint: t("pages.claimsPaymentMethod.choiceHintDebit"),
            value: PaymentPreferenceMethod.debit,
          },
        ]}
        label={t("pages.claimsPaymentMethod.sectionLabel")}
        type="radio"
      />

      <ConditionalContent
        visible={
          paymentPreference.payment_method === PaymentPreferenceMethod.ach
        }
      >
        <Fieldset>
          <FormLabel component="legend">
            {t("pages.claimsPaymentMethod.achSectionLabel")}
          </FormLabel>
          <Lead>{t("pages.claimsPaymentMethod.achLead")}</Lead>

          <InputText
            {...getFunctionalInputProps(
              "temp.payment_preferences[0].account_details.routing_number"
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
              "temp.payment_preferences[0].account_details.account_number"
            )}
            label={t("pages.claimsPaymentMethod.accountNumberLabel")}
            inputMode="numeric"
            smallLabel
            pii
          />
        </Fieldset>
      </ConditionalContent>

      <ConditionalContent
        visible={
          paymentPreference.payment_method === PaymentPreferenceMethod.debit
        }
      >
        <Alert state="info">
          {t("pages.claimsPaymentMethod.debitDestinationInfo")}
        </Alert>
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
