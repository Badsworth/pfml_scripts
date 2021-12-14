import React, { useEffect } from "react";
import withUser, { WithUserProps } from "../../../hoc/withUser";

import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/core/Heading";
import { OtherDocumentType } from "../../../models/Document";
import PageNotFound from "../../../components/PageNotFound";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Table from "../../../components/core/Table";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { createRouteWithQuery } from "../../../utils/routeWithParams";
import formatDate from "../../../utils/formatDate";
import formatDateRange from "../../../utils/formatDateRange";
import { getMaxBenefitAmount } from "../../../utils/getMaxBenefitAmount";
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
    documents: { documents: allClaimDocuments, loadAll: loadAllClaimDocuments },
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

  const application_id = claimDetail?.application_id;
  useEffect(() => {
    if (application_id) {
      loadAllClaimDocuments(application_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [application_id]);

  const hasNonDocumentsLoadError: boolean = items.some(
    (error) => error.name !== "DocumentsLoadError"
  );

  if (hasNonDocumentsLoadError) {
    return (
      <BackButton
        label={t("pages.payments.backButtonLabel")}
        href={routes.applications.index}
      />
    );
  }

  const documentsForApplication = allClaimDocuments.filterByApplication(
    application_id || ""
  );
  const approvalDate = documentsForApplication.find(
    (document: { document_type: string }) =>
      document.document_type === OtherDocumentType.approvalNotice
  )?.created_at;

  const isRetroactive =
    approvalDate && claimDetail
      ? claimDetail?.absence_periods[0]?.absence_period_end_date < approvalDate
      : false;

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
    t("pages.payments.paymentsTable.estimatedDateHeader"),
    t("pages.payments.paymentsTable.dateSentHeader"),
    t("pages.payments.paymentsTable.amountSentHeader"),
  ];

  const waitingWeek =
    claimDetail?.waitingWeek?.startDate &&
    formatDateRange(
      claimDetail.waitingWeek.startDate,
      claimDetail.waitingWeek.endDate
    );

  const isIntermittent =
    claimDetail?.absence_periods[0].period_type === "Intermittent";

  const isIntermittentUnpaid =
    isIntermittent &&
    isFeatureEnabled("claimantShowPaymentsPhaseTwo") &&
    claimDetail?.payments?.length === 0;

  const maxBenefitAmount = `$${getMaxBenefitAmount()}`;

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.payments.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <StatusNavigationTabs
          activePath={portalFlow.pathname}
          absence_id={absence_id}
        />

        <Title hidden>{t("pages.payments.paymentsTitle")}</Title>

        <section className="margin-y-5" data-testid="your-payments">
          {/* Heading section */}
          <Heading level="2" className="margin-bottom-3">
            {t("pages.payments.yourPayments")}
          </Heading>
          <section data-testid="your-payments-intro">
            <Trans
              i18nKey="pages.payments.paymentsIntro"
              tOptions={{
                context: `${
                  isIntermittentUnpaid
                    ? "Intermittent_Unpaid"
                    : isIntermittent
                    ? "Intermittent"
                    : isRetroactive
                    ? "NonIntermittent_Retro"
                    : "NonIntermittent_NonRetro"
                }`,
              }}
              components={{
                "contact-center-report-phone-link": (
                  <a
                    href={`tel:${t(
                      "shared.contactCenterReportHoursPhoneNumber"
                    )}`}
                  />
                ),
              }}
            />
          </section>

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
                          {formatDate(sent_to_bank_date).short() ||
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
                {waitingWeek && (
                  <tr>
                    <td
                      data-label={t(
                        "pages.payments.paymentsTable.waitingWeekHeader"
                      )}
                    >
                      {waitingWeek}
                    </td>
                    <td colSpan={4}>
                      <Trans
                        i18nKey="pages.payments.paymentsTable.waitingWeekText"
                        components={{
                          "waiting-week-link": (
                            <a
                              href={
                                routes.external.massgov
                                  .sevenDayWaitingPeriodInfo
                              }
                              rel="noopener noreferrer"
                              target="_blank"
                            />
                          ),
                        }}
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </section>

        {/* Changes to payments FAQ section */}
        <section className="margin-y-5" data-testid="changes-to-payments">
          <Heading level="2" className="margin-bottom-3">
            {t("pages.payments.changesToPaymentsHeading")}
          </Heading>

          <Accordion>
            <AccordionItem
              className="margin-y-2"
              heading={t("pages.payments.delaysToPaymentsScheduleQuestion")}
            >
              <Trans
                i18nKey="pages.payments.delaysToPaymentsScheduleAnswer"
                components={{
                  li: <li />,
                  ul: <ul />,
                }}
              />
            </AccordionItem>

            <AccordionItem
              className="margin-y-2"
              heading={t("pages.payments.changesToPaymentsAmountQuestion")}
            >
              <Trans
                i18nKey="pages.payments.changesToPaymentsAmountAnswer"
                values={{ maxBenefitAmount }}
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
              className="margin-y-2"
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

        <section className="margin-y-5" data-testid="helpSection">
          {/* Questions/Contact Us section */}
          <Heading level="2">{t("pages.payments.questionsHeader")}</Heading>
          <Trans
            i18nKey="pages.payments.questionsDetails"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
          {/* Feedback section */}
          <Heading level="2">{t("pages.payments.feedbackHeader")}</Heading>
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
