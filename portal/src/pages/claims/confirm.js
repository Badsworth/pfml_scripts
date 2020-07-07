import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import Claim from "../../models/Claim";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import useFormState from "../../hooks/useFormState";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const Confirm = (props) => {
  const { t } = useTranslation();
  const { formState } = useFormState(props.claim);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await props.appLogic.submitClaim(formState);
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form usa-form--large">
        <Title>{t("pages.claimsConfirm.title")}</Title>
        <p>{t("pages.claimsConfirm.explanation1")}</p>
        <p>{t("pages.claimsConfirm.explanation2")}</p>
        <Alert state="info" noIcon>
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
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(Confirm);
