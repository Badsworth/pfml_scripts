import withUser, { WithUserProps } from "../../../hoc/withUser";
import Alert from "../../../components/core/Alert";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/core/Button";
import FormLabel from "../../../components/core/FormLabel";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Cancel = (_props: WithUserProps) => {
  const { t } = useTranslation();

  /* eslint-disable require-await */
  const handleSubmit = async () => {
    // Do nothing for now
  };

  // TODO(PORTAL-2064): Remove claimantShowModifications feature flag
  if (!isFeatureEnabled("claimantShowModifications")) return <PageNotFound />;

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsModifySuccess.backButtonLabel")}
        href={routes.applications.index}
      />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title small>{t("pages.claimsModifyCancel.title")}</Title>
        <Alert state="warning" className="maxw-tablet">
          <Trans
            i18nKey="pages.claimsModifyCancel.overpaymentsWarning"
            components={{
              "overpayments-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.overpayments}
                />
              ),
            }}
          />
        </Alert>
        <FormLabel>{t("pages.claimsModifyCancel.sectionLabel")}</FormLabel>
        <p>{t("pages.claimsModifyCancel.cancelBody")}</p>
        <Button>{t("pages.claimsModifyCancel.cancelButton")}</Button>
      </form>
    </React.Fragment>
  );
};

export default withUser(Cancel);
