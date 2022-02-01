import {
  BenefitsApplicationDocument,
  DocumentType,
  findDocumentsByTypes,
} from "../../../models/Document";
import React, { useEffect } from "react";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import { AbsencePeriod } from "../../../models/AbsencePeriod";
import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import Alert from "../../../components/core/Alert";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import BackButton from "../../../components/BackButton";
import ClaimDetail from "src/models/ClaimDetail";
import Heading from "../../../components/core/Heading";
import LeaveReason from "../../../models/LeaveReason";
import PageNotFound from "../../../components/PageNotFound";
import Spinner from "../../../components/core/Spinner";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Table from "../../../components/core/Table";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { createRouteWithQuery } from "../../../utils/routeWithParams";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
import formatDate from "src/utils/formatDate";
import formatDateRange from "../../../utils/formatDateRange";
import isBlank from "../../../utils/isBlank";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

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
    claims: { claimDetail, loadClaimDetail, hasLoadedPayments },
    documents: {
      documents: allClaimDocuments,
      loadAll: loadAllClaimDocuments,
      hasLoadedClaimDocuments,
    },
    portalFlow,
  } = appLogic;

  const application_id = claimDetail?.application_id;
  const shouldLoad =
    !!absence_id &&
    (claimDetail?.fineos_absence_id !== absence_id ||
      !hasLoadedPayments(absence_id));

  useEffect(() => {
    if (shouldLoad) {
      loadClaimDetail(absence_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldLoad, absence_id]);

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

  // Check both because claimDetail could be cached from a different status page.
  if (shouldLoad || !hasLoadedClaimDocuments(application_id || "")) {
    return (
      <div className="text-center">
        <Spinner aria-label={t("pages.payments.loadingClaimDetailLabel")} />
      </div>
    );
  }
  /**
   * If there is no absence_id query parameter,
   * then return the PFML 404 page.
   */
  if (!absence_id || !claimDetail) return <PageNotFound />;

  const helper = paymentStatusViewHelper(claimDetail, allClaimDocuments);

  const {
    hasApprovedStatus,
    hasPendingStatus,
    hasPayments,
    hasWaitingWeek,
    hasApprovalNotice,
    checkbackDate,
    payments,
  } = helper;

  const infoAlertContext = getInfoAlertContext(helper);
  const checkbackDateContext = getPaymentIntroContext(helper);

  // Determines if phase two payment features are displayed
  const showPhaseTwoFeatures =
    isFeatureEnabled("claimantShowPaymentsPhaseTwo") && hasApprovedStatus;

  if (!showPhaseTwoFeatures || !hasApprovalNotice) {
    portalFlow.goTo(routes.applications.status.claim, {
      absence_id,
    });
  }

  const tableColumns = [
    t("pages.payments.tablePayPeriodHeader"),
    t("pages.payments.tableAmountHeader"),
    t("pages.payments.tableStatusHeader"),
  ];

  const shouldShowPaymentsTable =
    hasPayments || (hasWaitingWeek && showPhaseTwoFeatures);

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
      {infoAlertContext && (hasPendingStatus || hasApprovedStatus) && (
        <Alert
          className="margin-bottom-3"
          data-test="info-alert"
          heading={t("pages.payments.infoAlertHeading", {
            context: infoAlertContext,
          })}
          headingLevel="2"
          headingSize="4"
          noIcon
          state="info"
        >
          <p>
            <Trans
              i18nKey="pages.payments.infoAlertBody"
              tOptions={{ context: infoAlertContext }}
              components={{
                "about-bonding-leave-link": (
                  <a
                    href={
                      routes.external.massgov.benefitsGuide_aboutBondingLeave
                    }
                    target="_blank"
                    rel="noreferrer noopener"
                  />
                ),
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
              }}
            />
          </p>
        </Alert>
      )}

      <BackButton
        label={t("pages.payments.backButtonLabel")}
        href={routes.applications.index}
      />
      <Title hidden>{t("pages.payments.paymentsTitle")}</Title>
      <div className="measure-6">
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
                          {formatDateRange(period_start_date, period_end_date)}
                        </td>
                        <td data-label={tableColumns[1]}>
                          {getPaymentAmount(status, amount)}
                        </td>
                        <td data-label={tableColumns[2]}>
                          <Trans
                            i18nKey="pages.payments.tablePaymentStatus"
                            tOptions={{
                              context: getPaymentStatus(status, payment_method),
                              paymentMethod: getPaymentMethod(payment_method),
                              payPeriod: formatDateRange(
                                expected_send_date_start,
                                expected_send_date_end,
                                "and"
                              ),
                              sentDate:
                                dayjs(sent_to_bank_date).format("MMMM D, YYYY"),
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
                    <td data-label={t("pages.payments.tableWaitingWeekHeader")}>
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
    </React.Fragment>
  );
};

export default withUser(Payments);

type PaymentStatusViewHelper = ReturnType<typeof paymentStatusViewHelper>;

function paymentStatusViewHelper(
  claimDetail: ClaimDetail,
  documents: ApiResourceCollection<BenefitsApplicationDocument>
) {
  const {
    absence_periods: _absencePeriods,
    has_paid_payments: _isPaid,
    payments,
  } = claimDetail;

  // private variables
  const _absenceDetails = AbsencePeriod.groupByReason(_absencePeriods);
  const _hasBondingReason = LeaveReason.bonding in _absenceDetails;
  const _hasPregnancyReason = LeaveReason.pregnancy in _absenceDetails;
  const _hasNewBorn = _absencePeriods.some(
    (absenceItem: AbsencePeriod) =>
      absenceItem.reason_qualifier_one === "Newborn"
  );
  const _initialClaimStartDate =
    claimDetail.leaveDates[0].absence_period_start_date;
  const _fourteenthDayOfClaim = dayjs(_initialClaimStartDate)
    .add(14, "day")
    .format("YYYY-MM-DD");
  const _approvalNotice = findDocumentsByTypes(documents.items, [
    DocumentType.approvalNotice,
  ])[0];
  const _approvalDate = _approvalNotice?.created_at;

  // intermittent claims are treated differently in a few ways
  // 1. changes intro text
  // 2. the waiting week will never show in the payments
  //    table for intermittent claims.
  const isIntermittent = claimDetail.isIntermittent;

  // changes intro text
  const isContinuous = claimDetail.isContinuous;

  // 1. phase 1 & 2 will only be available for people with approved statuses
  // 2. info alerts, if any, should show if claim is approved
  const hasApprovedStatus = claimDetail.hasApprovedStatus;

  // info alerts, if any, should show if claim is pending
  const hasPendingStatus = claimDetail.hasPendingStatus;

  // changes InfoAlert text
  const onlyHasNewBornBondingReason =
    _hasBondingReason && !_hasPregnancyReason && _hasNewBorn;
  const onlyHasPregnancyReason = _hasPregnancyReason && !_hasBondingReason;

  // only show waiting period row in the payments table if there is a waiting week on the claim detail
  // intermittent claims never have waiting weeks.
  const hasWaitingWeek =
    !isBlank(claimDetail.waitingWeek?.startDate) && !isIntermittent;

  // 1. only show payments table if claimant has payments to show.
  // 2. changes intro text
  const hasPayments = !!payments.length;

  // changes intro text
  const isUnpaid = !_isPaid;

  // there is a 30 minute window between when the claim detail says the claim is approved
  // and the approval notice is available, we only want to display some content
  // if the user can also access the approval notice.
  const hasApprovalNotice = !!_approvalDate;

  // if payment is retroactive
  // and/or if the claim was approved within the first 14 days of the leave period
  // 1. changes intro text
  // 2. changes checkbackDate
  const isRetroactive = hasApprovalNotice
    ? _absencePeriods[_absencePeriods.length - 1]?.absence_period_end_date <
      _approvalDate
    : false;
  const isApprovedBeforeFourteenthDayOfClaim =
    _approvalDate < _fourteenthDayOfClaim;

  // for claims that have no payments and aren't intermittent
  // the date the user should come back to check their payment status
  // that shows in the intro text
  const checkbackDate = (function () {
    // intermittent claims or claims that have payments
    // should have no checkbackDate
    if (hasPayments || isIntermittent || !_approvalDate) {
      return null;
    }

    let result;
    if (isRetroactive || !isApprovedBeforeFourteenthDayOfClaim) {
      result = dayjs(_approvalDate).addBusinessDays(3);
    } else {
      result = dayjs(_initialClaimStartDate).add(14, "day").addBusinessDays(3);
    }

    return formatDate(result.format()).full();
  })();

  // intro text changes if there is a checkback date.
  const hasCheckbackDate = !!checkbackDate;

  return {
    payments,
    isIntermittent,
    isContinuous,
    hasApprovedStatus,
    hasPendingStatus,
    onlyHasNewBornBondingReason,
    onlyHasPregnancyReason,
    hasWaitingWeek,
    hasPayments,
    isUnpaid,
    hasApprovalNotice,
    isRetroactive,
    isApprovedBeforeFourteenthDayOfClaim,
    checkbackDate,
    hasCheckbackDate,
  };
}

function getInfoAlertContext(helper: PaymentStatusViewHelper) {
  const { onlyHasNewBornBondingReason, onlyHasPregnancyReason } = helper;
  if (onlyHasNewBornBondingReason) {
    return "bonding";
  }

  if (onlyHasPregnancyReason) {
    return "pregnancy";
  }

  return "";
}

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
