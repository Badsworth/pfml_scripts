import Alert from "../components/Alert";
import Button from "../components/Button";
import InputText from "../components/InputText";
import Title from "../components/Title";
import User from "../models/User"
import ClaimCollection from "../models/ClaimCollection";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import React from "react";
import PropTypes from "prop-types";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";
import withClaims from "../hoc/withClaims";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps"
import useThrottledHandler from "../hooks/useThrottledHandler"

export const ConvertToEmployer = (props) => {
  const { appLogic, claims, user } = props;
  const { t } = useTranslation();
  const { convertToEmployer } = appLogic.users;
  const { formState, updateFields } = useFormState({ employer_fein: "" });
  const hasClaims = !claims.isEmpty;

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await convertToEmployer(user.user_id, {
      employer_for_leave_admin: formState.employer_fein.replace("-", ""),
    });
  })

  return (
    <React.Fragment>
      <Title>{t("pages.convertToEmployer.title")}</Title>
      {hasClaims && (
        <Alert
          heading={t("pages.getReady.alertHeading")}
          state="info"
          neutral
          className="margin-bottom-3"
        >
          oh no u got claims tho
        </Alert>
      )}
      <div className="measure-6">
        <form className="usa-form" onSubmit={handleSubmit} method="post">
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
      convertToEmployer: PropTypes.func.isRequired
    }),
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
      goTo: PropTypes.func.isRequired
    }),
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection),
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

export default withClaims(ConvertToEmployer);
