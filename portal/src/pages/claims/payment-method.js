import Claim, { PaymentPreferenceMethod } from "../../models/Claim";
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

// TODO: Export full set of fields once Checklist no longer relies on
// this array for determining which steps are completed
export const fields = ["claim.temp.payment_preferences[0].payment_method"];

const PaymentMethod = (props) => {
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
          />

          <InputText
            {...getFunctionalInputProps(
              "temp.payment_preferences[0].account_details.account_number"
            )}
            label={t("pages.claimsPaymentMethod.accountNumberLabel")}
            inputMode="numeric"
            smallLabel
          />
        </Fieldset>
      </ConditionalContent>

      <ConditionalContent
        visible={
          paymentPreference.payment_method === PaymentPreferenceMethod.debit
        }
      >
        <Fieldset>
          <FormLabel component="legend">
            {t("pages.claimsPaymentMethod.debitSectionLabel")}
          </FormLabel>

          <InputText
            {...getFunctionalInputProps(
              "temp.payment_preferences[0].destination_address.line_1"
            )}
            label={t("pages.claimsPaymentMethod.addressLine1Label")}
            autoComplete="address-line1"
            smallLabel
          />

          <InputText
            {...getFunctionalInputProps(
              "temp.payment_preferences[0].destination_address.line_2"
            )}
            label={t("pages.claimsPaymentMethod.addressLine2Label")}
            optionalText={t("components.form.optional")}
            autoComplete="address-line2"
            smallLabel
          />

          <InputText
            {...getFunctionalInputProps(
              "temp.payment_preferences[0].destination_address.city"
            )}
            label={t("pages.claimsPaymentMethod.addressCityLabel")}
            autoComplete="address-level2"
            smallLabel
          />

          <InputText
            {...getFunctionalInputProps(
              "temp.payment_preferences[0].destination_address.state"
            )}
            label={t("pages.claimsPaymentMethod.addressStateLabel")}
            autoComplete="address-level1"
            smallLabel
          />

          <InputText
            {...getFunctionalInputProps(
              "temp.payment_preferences[0].destination_address.zip"
            )}
            label={t("pages.claimsPaymentMethod.addressZipLabel")}
            autoComplete="postal-code"
            inputMode="numeric"
            smallLabel
            width="medium"
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
