import React, { useEffect } from "react";
import {
  paymentStatusViewHelper,
  showPaymentsTab,
} from "src/utils/paymentsHelpers";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/core/Heading";
import PageNotFound from "../../../components/PageNotFound";
import { Payment } from "src/models/Payment";
import Spinner from "../../../components/core/Spinner";
import StatusNavigationTabs from "../../../features/claim-status-payments/StatusNavigationTabs";
import Table from "../../../components/core/Table";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { createRouteWithQuery } from "../../../utils/routeWithParams";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
import formatDateRange from "../../../utils/formatDateRange";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import StatusLayout from "src/features/claim-status-payments/status-layout";

// TODO(PORTAL-1482): remove test cases for checkback dates
// remove dayjs and dayjsBusinessTime imports
dayjs.extend(dayjsBusinessTime);

export const Payments = ({
  appLogic,
  query,
}: WithUserProps & {
  query: {
    absence_id?: string;
  };
}) => {
  const { t } = useTranslation();
  const { absence_id } = query;
  const {
    appErrors,
    claims: { claimDetail, loadClaimDetail },
    documents: {
      documents: allClaimDocuments,
      loadAll: loadAllClaimDocuments,
      hasLoadedClaimDocuments,
    },
    payments: { loadPayments, loadedPaymentsData, hasLoadedPayments },
    portalFlow,
  } = appLogic;

  const application_id = claimDetail?.application_id;

  useEffect(() => {
    if (absence_id) {
      loadClaimDetail(absence_id);
      loadPayments(absence_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absence_id]);

  useEffect(() => {
    if (application_id) {
      loadAllClaimDocuments(application_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [application_id]);

  if (appErrors.length > 0) {
    return (
      <BackButton
        label={t("pages.payments.backButtonLabel")}
        href={routes.applications.index}
      />
    );
  }

  /**
   * If there is no absence_id query parameter,
   * then return the PFML 404 page.
   */
  if (!absence_id || !claimDetail) return <PageNotFound />;

  // Check both because claimDetail could be cached from a different status page.
  if (
    claimDetail.fineos_absence_id !== absence_id ||
    !hasLoadedPayments(absence_id) ||
    !hasLoadedClaimDocuments(application_id || "")
  ) {
    return (
      <div className="text-center">
        <Spinner aria-label={t("pages.payments.loadingClaimDetailLabel")} />
      </div>
    );
  }

  const helper = paymentStatusViewHelper(
    claimDetail,
    allClaimDocuments,
    loadedPaymentsData || new Payment()
  );

  const { hasPayments, hasWaitingWeek, checkbackDate, payments } = helper;

  const checkbackDateContext = getPaymentIntroContext(helper);

  if (!showPaymentsTab(helper)) {
    portalFlow.goTo(routes.applications.status.claim, {
      absence_id,
    });
  }

  const tableColumns = [
    t("pages.payments.tablePayPeriodHeader"),
    t("pages.payments.tableAmountHeader"),
    t("pages.payments.tableStatusHeader"),
  ];

  const shouldShowPaymentsTable = hasPayments || hasWaitingWeek;

  const getPaymentAmount = (status: string, amount: number | null) => {
    if (status === "Sent to bank") {
      return t("pages.payments.tableAmountSent", { amount });
    } else if (status === "Pending") {
      return "Processing";
    }
    return status;
  };

  const getPaymentMethod = (payment_method: string) => {
    if (payment_method === "Check") {
      return "check";
    } else {
      return "direct deposit";
    }
  };

  const getPaymentStatus = (status: string, payment_method: string) => {
    if (status === "Sent to bank" && payment_method === "Check") {
      return "Check";
    } else {
      return status;
    }
  };

  return (
    <React.Fragment>
      <StatusLayout appLogic={appLogic}>
        <div className="measure-6">
          <Title hidden>{t("pages.payments.paymentsTitle")}</Title>
          <StatusNavigationTabs
            activePath={portalFlow.pathname}
            absence_id={absence_id}
          />

          <section className="margin-y-5" data-testid="your-payments">
            {/* Heading section */}
            <Heading level="2" size="1" className="margin-bottom-3">
              {t("pages.payments.yourPayments")}
            </Heading>
            <section data-testid="your-payments-intro">
              <Trans
                i18nKey="pages.payments.paymentsIntro"
                tOptions={{
                  context: checkbackDateContext,
                  checkbackDate,
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

            {/* Table section */}
            {shouldShowPaymentsTable && (
              <Table responsive>
                <thead>
                  <tr>
                    {shouldShowPaymentsTable &&
                      tableColumns.map((columnName) => (
                        <th key={columnName} scope="col">
                          {columnName}
                        </th>
                      ))}
                  </tr>
                </thead>
                <tbody>
                  {payments
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
                          <td
                            data-label={tableColumns[0]}
                            className="tablet:width-card-lg"
                          >
                            {formatDateRange(
                              period_start_date,
                              period_end_date
                            )}
                          </td>
                          <td data-label={tableColumns[1]}>
                            {getPaymentAmount(status, amount)}
                          </td>
                          <td data-label={tableColumns[2]}>
                            <Trans
                              i18nKey="pages.payments.tablePaymentStatus"
                              tOptions={{
                                context: getPaymentStatus(
                                  status,
                                  payment_method
                                ),
                                paymentMethod: getPaymentMethod(payment_method),
                                payPeriod: formatDateRange(
                                  expected_send_date_start,
                                  expected_send_date_end,
                                  "and"
                                ),
                                sentDate:
                                  dayjs(sent_to_bank_date).format(
                                    "MMMM D, YYYY"
                                  ),
                              }}
                              components={{
                                "delays-accordion-link": (
                                  <a href={"#delays_accordion"} />
                                ),
                              }}
                            />
                          </td>
                        </tr>
                      )
                    )}
                  {hasWaitingWeek && (
                    <tr>
                      <td
                        data-label={t("pages.payments.tableWaitingWeekHeader")}
                      >
                        {t("pages.payments.tableWaitingWeekGeneric")}
                      </td>
                      <td data-label={tableColumns[1]}>$0.00</td>
                      <td>
                        <Trans
                          i18nKey="pages.payments.tableWaitingWeekText"
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
              <div id="delays_accordion">
                <AccordionItem
                  className="margin-y-2"
                  heading={t("pages.payments.delaysToPaymentsScheduleQuestion")}
                >
                  <Trans
                    i18nKey="pages.payments.delaysToPaymentsScheduleAnswer"
                    components={{
                      "online-appeals-form": (
                        <a
                          href={routes.external.massgov.onlineAppealsForm}
                          target="_blank"
                          rel="noreferrer noopener"
                        />
                      ),
                      li: <li />,
                      ul: <ul />,
                    }}
                  />
                </AccordionItem>
              </div>

              <AccordionItem
                className="margin-y-2"
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
      </StatusLayout>
    </React.Fragment>
  );
};

export default withUser(Payments);

function getPaymentIntroContext(helper: PaymentStatusViewHelper) {
  const {
    hasCheckbackDate,
    isUnpaid,
    isIntermittent,
    isContinuous,
    isRetroactive,
    isApprovedBeforeFourteenthDayOfClaim,
  } = helper;

  if (isFeatureEnabled("claimantShowPaymentsPhaseTwo")) {
    /* Remove once phasetwo feature flag is removed */
    if (isUnpaid && isIntermittent) {
      return "Intermittent_Unpaid";
    }

    if (hasCheckbackDate) {
      /* Keys for text that include checkbackDate */
      const contextSuffix = isApprovedBeforeFourteenthDayOfClaim
        ? "PreFourteenthClaimDate"
        : isRetroactive
        ? "Retroactive"
        : "PostFourteenthClaimDate";
      return isContinuous
        ? `Continuous_${contextSuffix}`
        : `ReducedSchedule_${contextSuffix}`;
    }

    /* Remove once phasetwo feature flag is removed */
    return isIntermittent
      ? "Intermittent"
      : isRetroactive
      ? "NonIntermittent_Retro"
      : "NonIntermittent_NonRetro";
  }

  /* add intermittent_unpaid once phasetwo flag is removed */
  return isIntermittent
    ? "Intermittent"
    : isRetroactive
    ? "NonIntermittent_Retro"
    : "NonIntermittent_NonRetro";
}
