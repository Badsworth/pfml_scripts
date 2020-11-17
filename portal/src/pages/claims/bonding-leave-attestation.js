import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import Button from "../../components/Button";
import Claim from "../../models/Claim";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const BondingLeaveAttestation = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, query } = props;
  const handleSubmit = (event) => {
    event.preventDefault();
    appLogic.portalFlow.goToNextPage({ claim }, query);
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title>{t("pages.claimsBondingLeaveAttestation.title")}</Title>
        <Trans
          i18nKey="pages.claimsBondingLeaveAttestation.lead"
          components={{ ul: <ul className="usa-list" />, li: <li /> }}
        />
        <Alert className="measure-6" state="info" noIcon>
          <p>{t("pages.claimsBondingLeaveAttestation.truthAttestation")}</p>
          <Button type="submit">
            {t("pages.claimsBondingLeaveAttestation.submitApplicationButton")}
          </Button>
        </Alert>
      </form>
    </React.Fragment>
  );
};

BondingLeaveAttestation.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(Claim).isRequired,
  query: PropTypes.object.isRequired,
};

export default withClaim(BondingLeaveAttestation);
