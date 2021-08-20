import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const BondingLeaveAttestation = (props) => {
  const { t } = useTranslation();
  const { appLogic, query } = props;
  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.claimsBondingLeaveAttestation.title")}</Title>
      <Trans
        i18nKey="pages.claimsBondingLeaveAttestation.lead"
        components={{ ul: <ul className="usa-list" />, li: <li /> }}
      />
      <Alert className="measure-6" state="info" noIcon>
        <p>{t("pages.claimsBondingLeaveAttestation.truthAttestation")}</p>
        <ButtonLink
          className="text-no-underline text-white"
          href={appLogic.portalFlow.getNextPageRoute("CONTINUE", {}, query)}
        >
          {t("pages.claimsBondingLeaveAttestation.submitApplicationButton")}
        </ButtonLink>
      </Alert>
    </React.Fragment>
  );
};

BondingLeaveAttestation.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
    }),
  }).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(BondingLeaveAttestation);
