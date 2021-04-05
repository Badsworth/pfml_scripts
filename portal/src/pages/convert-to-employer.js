// import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
// import Alert from "../components/Alert";
import ButtonLink from "../components/ButtonLink";
import ClaimCollection from "../models/ClaimCollection";
// import Heading from "../components/Heading";
// import Icon from "../components/Icon";
// import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import InputText from "../components/InputText";
import Button from "../components/Button";
import { Trans } from "react-i18next";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";
import useFormState from "../hooks/useFormState";
import useFunctionalInputProps from "../hooks/useFunctionalInputProps"
import useThrottledHandler from "../hooks/useThrottledHandler"
import withClaims from "../hoc/withClaims";

export const ConvertToEmployer = (props) => {
  const { appLogic, claims, user } = props;
  const { t } = useTranslation();
  const { convertToEmployer } = appLogic.users;
  const { formState, updateFields } = useFormState({ employer_fein: "" });
  const hasClaims = !claims.isEmpty;
  const iconClassName =
    "margin-right-1 text-secondary text-middle margin-top-neg-05";
  /* const alertIconProps = {
    className: iconClassName,
    height: 20,
    width: 20,
    fill: "currentColor",
  };
 */
  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    console.log(user.user_id, formState, appLogic.users)
    await convertToEmployer(user.user_id, {
      employer_fein: formState.employer_fein.replace("-", ""),
    });
    // navigate to employer page
  })

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

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
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }),
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
};

export default withClaims(ConvertToEmployer);
