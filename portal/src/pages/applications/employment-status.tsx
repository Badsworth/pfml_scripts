import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Alert from "../../components/core/Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../../components/core/Details";
import { EmploymentStatus as EmploymentStatusEnum } from "../../models/BenefitsApplication";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputText from "../../components/core/InputText";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.employment_status", "claim.employer_fein"];

export const EmploymentStatus = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // TODO (CP-1281): Show employment status question when Portal supports other employment statuses
  const showEmploymentStatus = isFeatureEnabled("claimantShowEmploymentStatus");

  const initialFormState = pick(props, fields).claim || {
    employment_status: undefined,
  };

  if (!showEmploymentStatus) {
    // If the radio buttons are disabled, hard-code the field so that validations pass
    initialFormState.employment_status = EmploymentStatusEnum.employed;
  }

  const { formState, getField, updateFields, clearField } =
    useFormState(initialFormState);
  const employment_status = get(formState, "employment_status");

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const choiceKeys: Array<keyof typeof EmploymentStatusEnum> = [
    "employed",
    "unemployed",
    "selfEmployed",
  ];

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      {!showEmploymentStatus && (
        <Alert state="info" neutral>
          <Trans
            i18nKey="pages.claimsEmploymentStatus.alertBody"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
              p: <p />,
            }}
          />
        </Alert>
      )}

      {showEmploymentStatus && (
        <InputChoiceGroup
          {...getFunctionalInputProps("employment_status")}
          choices={choiceKeys.map((key) => ({
            checked: employment_status === EmploymentStatusEnum[key],
            label: t("pages.claimsEmploymentStatus.choiceLabel", {
              context: key,
            }),
            value: EmploymentStatusEnum[key],
          }))}
          label={t("pages.claimsEmploymentStatus.sectionLabel")}
          hint={
            <Details label={t("pages.claimsEmploymentStatus.furloughQuestion")}>
              {t("pages.claimsEmploymentStatus.furloughAnswer")}
            </Details>
          }
          type="radio"
        />
      )}

      <ConditionalContent
        fieldNamesClearedWhenHidden={["employer_fein"]}
        getField={getField}
        clearField={clearField}
        updateFields={updateFields}
        visible={employment_status === EmploymentStatusEnum.employed}
      >
        <InputText
          {...getFunctionalInputProps("employer_fein")}
          inputMode="numeric"
          label={t("pages.claimsEmploymentStatus.feinLabel")}
          mask="fein"
          hint={t("pages.claimsEmploymentStatus.feinHint")}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withBenefitsApplication(EmploymentStatus);
