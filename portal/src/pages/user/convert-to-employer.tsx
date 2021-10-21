import Alert from "../../components/Alert";
import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import Button from "../../components/Button";
import InputText from "../../components/InputText";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import User from "../../models/User";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplications from "../../hoc/withBenefitsApplications";

interface ConvertToEmployerProps {
  appLogic: AppLogic;
  claims: BenefitsApplicationCollection;
  user: User;
}

export const ConvertToEmployer = (props: ConvertToEmployerProps) => {
  const { appLogic, user, claims } = props;
  const { t } = useTranslation();
  const { convertUser } = appLogic.users;

  const { formState, updateFields } = useFormState({ employer_fein: "" });
  const hasClaims = !claims.isEmpty;
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await convertUser(user.user_id, {
      employer_fein: formState.employer_fein,
    });
  });

  if (user.hasEmployerRole) {
    // If user is already an employer, verifications is enabled, and the
    // employer is not verified, go to the verifications page.
    appLogic.portalFlow.goTo(
      routes.employers.organizations,
      {},
      { redirect: true }
    );
    return null;
  }

  // Do not allow conversion if user has created any claims at any point
  if (hasClaims) {
    appLogic.portalFlow.goToPageFor(
      "PREVENT_CONVERSION",
      {},
      {},
      { redirect: true }
    );
    return null;
  }

  return (
    <React.Fragment>
      <Title>{t("pages.convertToEmployer.title")}</Title>
      <Alert
        heading={t("pages.convertToEmployer.alertHeading")}
        state="warning"
        className="margin-bottom-3"
      >
        <p>{t("pages.convertToEmployer.alertDescription")}</p>
      </Alert>
      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <InputText
          {...getFunctionalInputProps("employer_fein")}
          inputMode="numeric"
          mask="fein"
          hint={
            <Trans
              i18nKey="pages.convertToEmployer.einHint"
              components={{
                "ein-link": (
                  <a
                    target="_blank"
                    rel="noopener"
                    href={routes.external.massgov.federalEmployerIdNumber}
                  />
                ),
              }}
            />
          }
          label={t("pages.convertToEmployer.einLabel")}
          smallLabel
        />
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.convertToEmployer.submit")}
        </Button>
      </form>
    </React.Fragment>
  );
};

export default withBenefitsApplications(ConvertToEmployer);
