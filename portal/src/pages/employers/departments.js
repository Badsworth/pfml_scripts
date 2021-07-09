import React, { useEffect, useState } from "react";
import { get, pick } from "lodash";

import Alert from "../../components/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Dropdown from "../../components/Dropdown";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import Spinner from "../../components/Spinner";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

/**
 * A form page to capture a user's attestation of having notified their employer.
 */
export const EmployerDepartment = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    appLogic.users.searchUsersDepartments({ tax_identifier: "" }).then(() => {
      setIsLoading(false);
    });
  }, []);

  return (
    <QuestionPage
      title={t("pages.claimsNotifiedEmployer.title")}
      // onSave={handleSave}
    >
      {isLoading ? (
        <Spinner aria-valuetext={t("components.spinner.label")} />
      ) : (
        <Dropdown
          choices={appLogic.users.departments.map((department) => {
            return {
              label: department,
              value: department,
            };
          })}
          emptyChoiceLabel="- Select a Department -"
          label="What is your Department?"
          name="department_id"
          onChange={() => {}}
          value="a"
        />
      )}
      {/* <InputChoiceGroup
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
      </ConditionalContent> */}
    </QuestionPage>
  );
};

EmployerDepartment.propTypes = {
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withUser(EmployerDepartment);
