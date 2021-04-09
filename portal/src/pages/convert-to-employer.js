import User, { RoleDescription } from "../models/User";
import Alert from "../components/Alert";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import Button from "../components/Button";
import ClaimCollection from "../models/ClaimCollection";
import InputText from "../components/InputText";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import { Trans } from "react-i18next";
import routes from "../routes";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";
import withClaims from "../hoc/withClaims";
import { isFeatureEnabled } from "../services/featureFlags";

export const ConvertToEmployer = (props) => {
  const { appLogic, user, claims } = props;
  const { t } = useTranslation();
  const { updateUser } = appLogic.users;
  const { formState, updateFields } = useFormState({ employer_fein: "" });
  const hasClaims = !claims.isEmpty;
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await updateUser(user.user_id, {
      role: { role_description: RoleDescription.employer },
      user_leave_administrator: {
        employer_fein: formState.employer_fein,
      },
    });
  });

  const showConvertToEmployer = isFeatureEnabled(
    "claimantConvertToEmployer"
  );

  // Do not allow access to this feature without feature flag
  if (!showConvertToEmployer) {
    appLogic.portalFlow.goTo(routes.applications.getReady);
    return null;
  }
  // Do not allow access without being logged in
  if (typeof user === "undefined") {
    appLogic.portalFlow.goTo(routes.auth.login);
    return null;
  }
  // If user is already an employer, go directly to employer welcome page
  if (user.hasEmployerRole) {
    appLogic.portalFlow.goTo(routes.employers.welcome);
    return null;
  }
  // Do not allow conversion if user has created claims and got sent to fineos
  if (hasClaims) {
    appLogic.portalFlow.goTo(routes.applications.getReady);
    return null;
  }

  return (
    <React.Fragment>
      <Title>{t("pages.convertToEmployer.title")}</Title>
      <Alert
        heading={t("pages.convertToEmployer.alertHeading")}
        state="warning"
        neutral
        className="margin-bottom-3"
      >
        {t("pages.convertToEmployer.alertDescription")}
      </Alert>
      <div className="measure-6">
        <form
          className="usa-form"
          onSubmit={handleSubmit}
          method="post"
          data-cy="fein-form"
        >
          <InputText
            {...getFunctionalInputProps("employer_fein")}
            inputMode="numeric"
            mask="fein"
            hint={
              <Trans
                i18nKey="pages.employersAuthCreateAccount.einHint"
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
            label={t("pages.employersAuthCreateAccount.einLabel")}
            smallLabel
            dataCy="fein-input"
          />
          <Button type="submit" loading={handleSubmit.isThrottled}>
            {t("pages.convertToEmployer.submit")}
          </Button>
        </form>
      </div>
    </React.Fragment>
  );
};

ConvertToEmployer.propTypes = {
  appLogic: PropTypes.shape({
    users: PropTypes.shape({
      updateUser: PropTypes.func.isRequired,
    }),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }),
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

export default withClaims(ConvertToEmployer);
