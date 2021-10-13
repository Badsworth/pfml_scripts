import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

export const Start = (props) => {
  const { t } = useTranslation();

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await props.appLogic.benefitsApplications.create();
  });

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form" method="post">
        <Title>{t("pages.claimsStart.title")}</Title>
        <Trans
          i18nKey="pages.claimsStart.explanation"
          components={{
            "mass-consent-agreement-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.consentAgreement}
              />
            ),
          }}
        />
        {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element[]; className: string; st... Remove this comment to see the full error message */}
        <Alert className="measure-6" state="info" noIcon>
          <p>{t("pages.claimsStart.truthAttestation")}</p>
          <Button
            type="submit"
            name="new-claim"
            loading={handleSubmit.isThrottled}
          >
            {t("pages.claimsStart.submitApplicationButton")}
          </Button>
        </Alert>
      </form>
    </React.Fragment>
  );
};

Start.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Start);
