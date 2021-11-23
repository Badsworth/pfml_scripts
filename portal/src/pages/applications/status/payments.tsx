import React, { useEffect } from "react";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/core/Heading";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Table from "../../../components/core/Table";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { createRouteWithQuery } from "../../../utils/routeWithParams";
import formatDateRange from "../../../utils/formatDateRange";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

interface PaymentsProps {
  query: {
    absence_id?: string;
  };
}

export const Payments = ({
  appLogic: {
    claims: { claimDetail, loadClaimDetail },
    portalFlow,
  },
  query: { absence_id },
}: WithUserProps & PaymentsProps) => {
  const { t } = useTranslation();

  useEffect(() => {
    if (absence_id) {
      loadClaimDetail(absence_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absence_id]);

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowPayments")) {
      portalFlow.goTo(routes.applications.status.claim, {
        absence_id,
      });
    }
  }, [portalFlow, absence_id]);

  const tableColumns = [
    t("pages.payments.paymentsTable.leaveDatesHeader"),
    t("pages.payments.paymentsTable.paymentMethodHeader"),
    t("pages.payments.paymentsTable.estimatedScheduledDateHeader"),
    t("pages.payments.paymentsTable.dateSentHeader"),
    t("pages.payments.paymentsTable.amountSentHeader"),
  ];
  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <StatusNavigationTabs
          activePath={portalFlow.pathname}
          absence_id={absence_id}
        />

        <Title hidden>{t("pages.claimsStatus.paymentsTitle")}</Title>

        {/* Heading section */}
        <Heading level="2" size="1">
          {t("pages.claimsStatus.yourPayments")}
        </Heading>

        <Table borderlessMobile responsiveIncludeHeader>
          <thead>
            <tr>
              {tableColumns.map((columnName) => (
                <th key={columnName} scope="col">
                  {columnName}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {claimDetail?.payments.map(
              ({
                payment_id,
                period_start_date,
                period_end_date,
                amount,
                sent_to_bank_date,
                payment_method,
                expected_send_date_start,
                expected_send_date_end,
                status,
              }) => (
                <tr key={payment_id}>
                  <td data-label={tableColumns[0]}>
                    {formatDateRange(period_start_date, period_end_date)}
                  </td>
                  <td data-label={tableColumns[1]}>
                    {t("pages.payments.paymentsTable.paymentMethod", {
                      context: payment_method,
                    })}
                  </td>
                  <td data-label={tableColumns[2]}>
                    {sent_to_bank_date
                      ? t("pages.payments.paymentsTable.paymentStatus", {
                          context: status,
                        })
                      : formatDateRange(
                          expected_send_date_start,
                          expected_send_date_end
                        )}
                  </td>
                  <td data-label={tableColumns[3]}>
                    {sent_to_bank_date ||
                      t("pages.payments.paymentsTable.paymentStatus", {
                        context: status,
                      })}
                  </td>
                  <td data-label={tableColumns[4]}>
                    {amount === null
                      ? t("pages.payments.paymentsTable.paymentStatus", {
                          context: status,
                        })
                      : t("pages.payments.paymentsTable.amountSent", {
                          amount,
                        })}
                  </td>
                </tr>
              )
            )}
          </tbody>
        </Table>

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
