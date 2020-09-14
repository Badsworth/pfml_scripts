import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { useTranslation } from "../../locales/i18n";

export const Start = (props) => {
  const { t } = useTranslation();

  const handleSubmit = async (event) => {
    event.preventDefault();
    await props.appLogic.claims.create();
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title>{t("pages.claimsStart.title")}</Title>
        <p>{t("pages.claimsStart.explanation1")}</p>
        <p>{t("pages.claimsStart.explanation2")}</p>
        <Alert className="measure-6" state="info" noIcon>
          {t("pages.claimsStart.truthAttestation")}
        </Alert>
        <Button type="submit" name="new-claim">
          {t("pages.claimsStart.submitApplicationButton")}
        </Button>
      </form>
    </React.Fragment>
  );
};

Start.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default Start;
