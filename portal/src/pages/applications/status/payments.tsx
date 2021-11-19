import React, { useEffect } from "react";
import withUser, { WithUserProps } from "../../../hoc/withUser";

import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/core/Heading";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { createRouteWithQuery } from "../../../utils/routeWithParams";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

interface PaymentsProps {
  query: {
    absence_id?: string;
  };
}

export const Payments = ({
  appLogic,
  query: { absence_id },
}: WithUserProps & PaymentsProps) => {
  const { t } = useTranslation();

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowPayments")) {
      appLogic.portalFlow.goTo(routes.applications.status.claim, {
        absence_id,
      });
    }
  }, [appLogic.portalFlow, absence_id]);

  // Determine leave type
  const isContinuous = appLogic.claims.claimDetail?.isContinuous;
  const isIntermittent = appLogic.claims.claimDetail?.isIntermittent;
  const isReducedSchedule = appLogic.claims.claimDetail?.isReducedSchedule;

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <StatusNavigationTabs
          activePath={appLogic.portalFlow.pathname}
          absence_id={absence_id}
        />

        <Title hidden>{t("pages.claimsStatus.paymentsTitle")}</Title>

        {/* Heading section */}
        <Heading level="2" size="1">
          {t("pages.claimsStatus.yourPayments")}
        </Heading>

        {/* When to expect payment section */}
        <section className="margin-y-4" data-testid="when-to-expect-payments">
          {(isContinuous || isReducedSchedule) && (
            <Trans
              components={{
                "waiting-period-info": (
                  <a
                    href={routes.external.massgov.sevenDayWaitingPeriodInfo}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
              }}
              i18nKey="pages.payments.whenToExpectPaymentContinuous"
            />
          )}

          {isReducedSchedule && (
            <Trans i18nKey="pages.payments.whenToExpectPaymentReducedSchedule" />
          )}

          {isIntermittent && (
            <Trans
              components={{
                "waiting-period-info": (
                  <a
                    href={routes.external.massgov.sevenDayWaitingPeriodInfo}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                "contact-center-report-hours-phone-link": (
                  <a
                    href={`tel:${t(
                      "shared.contactCenterReportHoursPhoneNumber"
                    )}`}
                  />
                ),
              }}
              i18nKey="pages.payments.whenToExpectPaymentIntermittent"
            />
          )}
        </section>

        {/* Changes to payments FAQ section */}
        <section className="margin-y-4" data-testid="changes-to-payments">
          <Accordion>
            <AccordionItem
              heading={t("pages.payments.changesToPaymentsScheduleQuestion")}
            >
              <Trans
                i18nKey="pages.payments.changesToPaymentsScheduleAnswer"
                components={{
                  li: <li />,
                  ul: <ul />,
                }}
              />
            </AccordionItem>

            <AccordionItem
              heading={t("pages.payments.changesToPaymentsAmountQuestion")}
            >
              <Trans
                i18nKey="pages.payments.changesToPaymentsAmountAnswer"
                components={{
                  li: <li />,
                  ul: <ul />,
                  "using-other-leave-link": (
                    <a
                      href={routes.external.massgov.usingOtherLeave}
                      target="_blank"
                      rel="noopener noreferrer"
                    />
                  ),
                  "view-notices-link": (
                    <a
                      href={createRouteWithQuery(
                        routes.applications.status.claim,
                        { absence_id },
                        "view_notices"
                      )}
                    />
                  ),
                }}
              />
            </AccordionItem>

            <AccordionItem
              heading={t(
                "pages.payments.changesToPaymentsYourPreferencesQuestion"
              )}
            >
              <Trans
                i18nKey="pages.payments.changesToPaymentsYourPreferencesAnswer"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
            </AccordionItem>
          </Accordion>
        </section>

        {/* Questions/Contact Us section */}
        <section className="margin-y-4" data-testid="questions">
          <Heading className="margin-bottom-2" level="3">
            {t("pages.payments.questionsHeader")}
          </Heading>
          <Trans
            i18nKey="pages.payments.questionsDetails"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        </section>
      </div>
    </React.Fragment>
  );
};

export default withUser(Payments);
