import Alert from "../../components/Alert";
import Claim from "../../models/Claim";
import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
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
  "claim.leave_details.employer_notified",
  "claim.leave_details.employer_notification_date",
];

/**
 * A form page to capture a user's attestation of having notified their employer.
 */
export const NotifiedEmployer = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, getField, updateFields, removeField } = useFormState(
    pick(props, fields).claim
  );
  const employer_notified = get(formState.leave_details, "employer_notified");

  const handleSave = () =>
    appLogic.claims.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsNotifiedEmployer.title")}
      onSave={handleSave}
    >
      <Alert state="info">
        {t("pages.claimsNotifiedEmployer.multipleEmployerAppAlert")}
      </Alert>

      <InputChoiceGroup
        {...getFunctionalInputProps("leave_details.employer_notified")}
        choices={[
          {
            checked: employer_notified === true,
            label: t("pages.claimsNotifiedEmployer.choiceYes"),
            value: "true",
          },
          {
            checked: employer_notified === false,
            label: t("pages.claimsNotifiedEmployer.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsNotifiedEmployer.sectionLabel")}
        hint={t("pages.claimsNotifiedEmployer.hint")}
        type="radio"
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "leave_details.employer_notification_date",
        ]}
        getField={getField}
        updateFields={updateFields}
        removeField={removeField}
        visible={employer_notified === true}
      >
        <InputDate
          {...getFunctionalInputProps(
            "leave_details.employer_notification_date"
          )}
          label={t("pages.claimsNotifiedEmployer.employerNotificationLabel")}
          hint={t("pages.claimsNotifiedEmployer.employerNotificationDateHint")}
          example={t("components.form.dateInputExample")}
          dayLabel={t("components.form.dateInputDayLabel")}
          monthLabel={t("components.form.dateInputMonthLabel")}
          yearLabel={t("components.form.dateInputYearLabel")}
        />
      </ConditionalContent>
      <ConditionalContent visible={employer_notified === false}>
        <Alert state="warning" role="alert">
          {t("pages.claimsNotifiedEmployer.mustNotifyEmployerWarning")}
        </Alert>
      </ConditionalContent>
    </QuestionPage>
  );
};

NotifiedEmployer.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(NotifiedEmployer);
