import React, { useEffect } from "react";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/core/Heading";
import PageNotFound from "../../../components/PageNotFound";
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
    appErrors: { items },
    claims: { claimDetail, loadClaimDetail, hasLoadedPayments },
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

  /**
   * If there is no absence_id query parameter,
   * then return the PFML 404 page.
   */
  const isAbsenceCaseId = Boolean(absence_id?.length);
  if (!isAbsenceCaseId) return <PageNotFound />;

  const shouldShowPaymentsTable =
    claimDetail?.payments !== null ||
    (hasLoadedPayments(absence_id || "") && !items.length);

  const tableColumns = [
    t("pages.payments.paymentsTable.leaveDatesHeader"),
    t("pages.payments.paymentsTable.paymentMethodHeader"),
    t("pages.payments.paymentsTable.estimatedScheduledDateHeader"),
    t("pages.payments.paymentsTable.dateSentHeader"),
    t("pages.payments.paymentsTable.amountSentHeader"),
  ];

  const waitingWeek =
    claimDetail?.waitingWeek?.startDate &&
    formatDateRange(
      claimDetail.waitingWeek.startDate,
      claimDetail.waitingWeek.endDate
    );

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

        <Trans i18nKey="pages.payments.paymentsIntro" />
        {shouldShowPaymentsTable && (
          <Table className="width-full" responsive>
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
              {claimDetail?.payments
                .reverse()
                .map(
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
                        {status !== "Pending"
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
              <tr>
                <td>{waitingWeek}</td>
                <td colSpan={4}>
                  <Trans
                    i18nKey="pages.payments.paymentsTable.waitingWeekText"
                    components={{
                      "waiting-week-link": (
                        <a
                          href={
                            routes.external.massgov.sevenDayWaitingPeriodInfo
                          }
                        />
                      ),
                    }}
                  />
                </td>
              </tr>
            </tbody>
          </Table>
        )}

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
                  "benefit-amount-details-link": (
                    <a
                      href={
                        routes.external.massgov
                          .benefitsGuide_benefitsAmountDetails
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                    />
                  ),
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

        <section className="margin-y-6" data-testid="helpSection">
          {/* Questions/Contact Us section */}
          <Heading level="3">{t("pages.payments.questionsHeader")}</Heading>
          <Trans
            i18nKey="pages.payments.questionsDetails"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
          {/* Feedback section */}
          <Heading level="3">{t("pages.payments.feedbackHeader")}</Heading>
          <Trans
            i18nKey="pages.payments.feedbackDetails"
            components={{
              "feedback-link": (
                <a
                  href={routes.external.massgov.feedbackClaimant}
                  target="_blank"
                  rel="noopener noreferrer"
                />
              ),
            }}
          />
        </section>
      </div>
    </React.Fragment>
  );
};

export default withUser(Payments);
