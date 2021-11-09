import React, { useEffect } from "react";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/Heading";
import LeaveReason from "../../../models/LeaveReason";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Title from "../../../components/Title";
import findKeyByValue from "../../../utils/findKeyByValue";
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

  const absenceDetails = claimDetail?.absencePeriodsByReason;
  const [firstAbsenceDetail] = absenceDetails
    ? Object.keys(absenceDetails)
    : [];
  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <Title weight="normal" small>
          {t("pages.claimsStatus.applicationDetails")}
        </Title>

        {/* Heading section */}

        <Heading level="2" size="1">
          {t("pages.claimsStatus.leaveReasonValueHeader", {
            context: findKeyByValue(LeaveReason, firstAbsenceDetail),
          })}
        </Heading>
        <div className="bg-base-lightest padding-2 tablet:display-flex tablet:padding-bottom-0">
          <div className="padding-bottom-3 padding-right-6">
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.applicationID")}
            </Heading>
            <p className="text-bold">{query.absence_id}</p>
          </div>
          <div>
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.employerEIN")}
            </Heading>
            <p className="text-bold">{claimDetail?.employer?.employer_fein}</p>
          </div>
        </div>
        <StatusNavigationTabs
          activePath={appLogic.portalFlow.pathname}
          absence_id={query.absence_id}
        />
      </div>
    </React.Fragment>
  );
};

export default withUser(Payments);
