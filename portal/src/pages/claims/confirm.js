import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import Claim from "../../models/Claim";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const Confirm = (props) => {
  const { claim } = props;
  const { t } = useTranslation();

  const handleSubmit = async (event) => {
    event.preventDefault();
    await props.appLogic.claims.submit(claim.application_id);
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title>{t("pages.claimsConfirm.title")}</Title>
        <p>{t("pages.claimsConfirm.explanation1")}</p>
        <p>{t("pages.claimsConfirm.explanation2")}</p>
        <Alert className="measure-6" state="info" noIcon>
          {t("pages.claimsConfirm.truthAttestation")}
        </Alert>
        <input
          className="usa-button"
          type="submit"
          value={t("pages.claimsConfirm.submitApplicationButton")}
        />
      </form>
    </React.Fragment>
  );
};

Confirm.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(Claim),
};

export default withClaim(Confirm);
