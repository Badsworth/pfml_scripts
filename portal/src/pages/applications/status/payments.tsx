import React, { useEffect } from "react";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/Heading";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Title from "../../../components/Title";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Payments = ({
  appLogic,
  query,
}: WithUserProps & { query: { absence_id?: string } }) => {
  const {
    claims: { claimDetail },
    portalFlow,
  } = appLogic;
  const { t } = useTranslation();

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowStatusPage") || !claimDetail) {
      portalFlow.goTo(routes.applications.status.claim, {
        absence_id: query.absence_id,
      });
    }
  }, [portalFlow, claimDetail, query.absence_id]);

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <StatusNavigationTabs
          activePath={appLogic.portalFlow.pathname}
          absence_id={query.absence_id}
        />

        <Title hidden>{t("pages.claimsStatus.paymentsTitle")}</Title>

        {/* Heading section */}
        <Heading level="2" size="1">
          {t("pages.claimsStatus.yourPayments")}
        </Heading>
      </div>
    </React.Fragment>
  );
};

export default withUser(Payments);
