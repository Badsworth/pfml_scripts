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

interface SectionWrapperProps {
  children: React.ReactNode;
  heading: string;
}

const SectionWrapper = ({ children, heading }: SectionWrapperProps) => {
  return (
    <section className="margin-y-4">
      <Heading className="margin-bottom-2" level="3">
        {heading}
      </Heading>

      {children}
    </section>
  );
};

export const Payments = ({
  appLogic,
  query,
}: WithUserProps & {
  query: {
    absence_id?: string;
  };
}) => {
  const { t } = useTranslation();
  const { portalFlow } = appLogic;

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowPayments")) {
      portalFlow.goTo(routes.applications.status.claim, {
        absence_id: query.absence_id,
      });
    }
  }, [portalFlow, query.absence_id]);

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

        {/* Changes to payments FAQ section */}
        <SectionWrapper heading={t("pages.payments.changesToPaymentsHeader")}>
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
                  "view-notices-link": (
                    <a
                      href={createRouteWithQuery(
                        routes.applications.status.claim,
                        { absence_id: query.absence_id },
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
        </SectionWrapper>

        {/* Questions/Contact Us section */}
        <SectionWrapper heading={t("pages.payments.questionsHeader")}>
          <Trans
            i18nKey="pages.payments.questionsDetails"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        </SectionWrapper>
      </div>
    </React.Fragment>
  );
};

export default withUser(Payments);
