import { get, pick } from "lodash";
import Alert from "../../components/Alert";
import BenefitsApplication from "../../models/BenefitsApplication";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

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

  const { formState, getField, updateFields, clearField } = useFormState(
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
      <InputChoiceGroup
        {...getFunctionalInputProps("leave_details.employer_notified")}
        hint={
          <Details
            label={t(
              "pages.claimsNotifiedEmployer.bondingRegsEmployerNotifiedDetailsLabel"
            )}
          >
            <Trans
              i18nKey="pages.claimsNotifiedEmployer.bondingRegsEmployerNotifiedDetailsSummary"
              components={{
                "emergency-bonding-regs-worker-link": (
                  <a
                    target="_blank"
                    rel="noopener"
                    href={
                      routes.external.massgov.emergencyBondingRegulationsWorker
                    }
                  />
                ),
              }}
            />
          </Details>
        }
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
        type="radio"
      />
      <ConditionalContent
        fieldNamesClearedWhenHidden={[
          "leave_details.employer_notification_date",
        ]}
        getField={getField}
        updateFields={updateFields}
        clearField={clearField}
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
        <Alert state="warning" role="alert" autoWidth>
          {t("pages.claimsNotifiedEmployer.mustNotifyEmployerWarning")}
        </Alert>
      </ConditionalContent>
    </QuestionPage>
  );
};

NotifiedEmployer.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withBenefitsApplication(NotifiedEmployer);
