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
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";
import withClaim from "../../hoc/withClaim";

export const fields = [
  "leave_details.employer_notified",
  "leave_details.employer_notification_date",
];

/**
 * A form page to capture a user's attestation of having notified their employer.
 */
export const NotifiedEmployer = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const { formState, updateFields, removeField } = useFormState(
    pick(claim, fields)
  );
  const { leave_details } = formState;
  const employer_notified = get(leave_details, "employer_notified");
  const handleInputChange = useHandleInputChange(updateFields);

  const handleSave = () => {
    appLogic.updateClaim(claim.application_id, formState);
  };

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsNotifiedEmployer.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
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
        name="leave_details.employer_notified"
        onChange={handleInputChange}
        type="radio"
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "leave_details.employer_notification_date",
        ]}
        removeField={removeField}
        visible={employer_notified === true}
      >
        <InputDate
          name="leave_details.employer_notification_date"
          label={t("pages.claimsNotifiedEmployer.employerNotificationLabel")}
          value={valueWithFallback(
            get(leave_details, "employer_notification_date")
          )}
          hint={t("pages.claimsNotifiedEmployer.employerNotificationDateHint")}
          dayLabel={t("components.form.dateInputDayLabel")}
          monthLabel={t("components.form.dateInputMonthLabel")}
          yearLabel={t("components.form.dateInputYearLabel")}
          onChange={handleInputChange}
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
