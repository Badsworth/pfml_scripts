import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import React from "react";
import Title from "../../components/Title";
import routes from "../../routes";
import { useRouter } from "next/router";
import { useTranslation } from "../../locales/i18n";

export const Confirm = () => {
  const { t } = useTranslation();
  const router = useRouter();

  const nextPage = routes.home;

  // TODO Update to submit application via API
  const handleSubmit = async (event) => {
    event.preventDefault();
    router.push(nextPage);
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

export default Confirm;
