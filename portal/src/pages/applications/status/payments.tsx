import React, { useEffect } from "react";

import { AbsencePeriod } from "../../../models/AbsencePeriod";
import Accordion from "../../../components/core/Accordion";
import AccordionItem from "../../../components/core/AccordionItem";
import Alert from "../../../components/core/Alert";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/core/Heading";
import LeaveReason from "../../../models/LeaveReason";
import { OtherDocumentType } from "../../../models/Document";
import StatusNavigationTabs from "../../../components/status/StatusNavigationTabs";
import Table from "../../../components/core/Table";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { WithUserProps } from "../../../hoc/withUser";
import { createRouteWithQuery } from "../../../utils/routeWithParams";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
import formatDate from "../../../utils/formatDate";
import formatDateRange from "../../../utils/formatDateRange";
import { getMaxBenefitAmount } from "../../../utils/getMaxBenefitAmount";
import isBlank from "../../../utils/isBlank";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";
import withClaimDetail from "src/hoc/withClaimDetail";

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
    appErrors: { items },
    claims: {
      claimDetail,
      loadClaimDetail,
      loadedPaymentsData,
      hasLoadedPayments,
    },
    documents: { documents: allClaimDocuments },
    portalFlow,
  } = appLogic;

  const hasPaidPayments = claimDetail?.has_paid_payments;

  // Determines if phase one payment features are displayed
  const showPhaseOneFeatures =
    isFeatureEnabled("claimantShowPayments") &&
    claimDetail?.hasApprovedStatus &&
    hasPaidPayments;

  // Determines if phase two payment features are displayed
  const showPhaseTwoFeatures =
    isFeatureEnabled("claimantShowPaymentsPhaseTwo") &&
    claimDetail?.hasApprovedStatus;

  const application_id = claimDetail?.application_id || "";
  const absencePeriods = claimDetail?.absence_periods || [];
  const absenceId = absence_id;

  const initialClaimStartDate =
    claimDetail?.leaveDates[0].absence_period_start_date;
  useEffect(() => {
    const loadPayments = (absenceId: string) =>
      !hasLoadedPayments(absenceId) ||
      (loadedPaymentsData?.absence_case_id &&
        Boolean(claimDetail?.payments.length === 0));

    if (claimDetail && !showPhaseOneFeatures && !showPhaseTwoFeatures) {
      portalFlow.goTo(routes.applications.status.claim, {
        absence_id,
      });
    } else if (
      absenceId &&
      (!claimDetail || Boolean(loadPayments(absenceId))) &&
      !items.find((item) => item.name === "NotFoundError")
    ) {
      loadClaimDetail(absence_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    absence_id,
    initialClaimStartDate,
    absenceId,
    loadedPaymentsData?.absence_case_id,
  ]);

  const absenceDetails = AbsencePeriod.groupByReason(absencePeriods);
  const hasPendingStatus = absencePeriods.some(
    (absenceItem) => absenceItem.request_decision === "Pending"
  );
  const hasApprovedStatus = absencePeriods.some(
    (absenceItem) => absenceItem.request_decision === "Approved"
  );
  const documentsForApplication =
    allClaimDocuments.filterByApplication(application_id);

  const getInfoAlertContext = (absenceDetails: {
    [reason: string]: AbsencePeriod[];
  }) => {
    const hasBondingReason = LeaveReason.bonding in absenceDetails;
    const hasPregnancyReason = LeaveReason.pregnancy in absenceDetails;
    const hasNewBorn = absencePeriods.some(
      (absenceItem) => absenceItem.reason_qualifier_one === "Newborn"
    );
    if (hasBondingReason && !hasPregnancyReason && hasNewBorn) {
      return "bonding";
    }

    if (hasPregnancyReason && !hasBondingReason) {
      return "pregnancy";
    }

    return "";
  };

  const infoAlertContext = getInfoAlertContext(absenceDetails);

  const approvalDate = documentsForApplication.find(
    (document: { document_type: string }) =>
      document.document_type === OtherDocumentType.approvalNotice
  )?.created_at;

  const isRetroactive = approvalDate
    ? absencePeriods[absencePeriods.length - 1]?.absence_period_end_date <
      approvalDate
    : false;

  const shouldShowPaymentsTable =
    Boolean(claimDetail?.payments?.length) ||
    (hasLoadedPayments(absence_id || "") && !items.length);

  const tableColumns = [
    t("pages.payments.paymentsTable.leaveDatesHeader"),
    t("pages.payments.paymentsTable.paymentMethodHeader"),
    t("pages.payments.paymentsTable.estimatedDateHeader"),
    t("pages.payments.paymentsTable.dateProcessedHeader"),
    t("pages.payments.paymentsTable.amountSentHeader"),
  ];

  const waitingWeek = !isBlank(claimDetail?.waitingWeek?.startDate);

  const isIntermittent = claimDetail?.isIntermittent;

  const isIntermittentUnpaid =
    isIntermittent &&
    isFeatureEnabled("claimantShowPaymentsPhaseTwo") &&
    !hasPaidPayments;

  const maxBenefitAmount = `$${getMaxBenefitAmount()}`;

  // TODO(PORTAL-1482): remove test cases for checkback dates

  let checkbackDate;
  let checkbackDateContext = isIntermittentUnpaid
    ? "Intermittent_Unpaid"
    : isIntermittent
    ? "Intermittent"
    : isRetroactive
    ? "NonIntermittent_Retro"
    : "NonIntermittent_NonRetro";

  if (
    isFeatureEnabled("claimantShowPaymentsPhaseTwo") &&
    !isIntermittent &&
    !hasPaidPayments
  ) {
    if (!hasPaidPayments && approvalDate) {
      checkbackDateContext = claimDetail?.isContinuous
        ? "Continuous_"
        : "ReducedSchedule_";
      const fourteenthDayOfClaim = dayjs(initialClaimStartDate)
        .add(13, "day")
        .format("YYYY-MM-DD");

      if (isRetroactive || approvalDate >= fourteenthDayOfClaim) {
        checkbackDate = dayjs(approvalDate)
          .addBusinessDays(3)
          .format("MM/DD/YYYY");
        checkbackDateContext += isRetroactive
          ? "Retroactive"
          : "PostFourteenthClaimDate";
      } else {
        checkbackDate = dayjs(initialClaimStartDate)
          .add(13, "day")
          .addBusinessDays(3)
          .format("MM/DD/YYYY");
        checkbackDateContext += "PreFourteenthClaimDate";
      }
    }
  }

  return (
    <React.Fragment>
      {!!infoAlertContext && (hasPendingStatus || hasApprovedStatus) && (
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
            {/* Estimated Date section */}
            <section className="margin-y-5" data-testid="estimated-date">
              <Heading level="3">
                {t("pages.payments.estimatedDateHeading")}
              </Heading>
              <p>{t("pages.payments.estimatedDate")}</p>
            </section>
          </section>

          {/* Table section */}
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
                {waitingWeek && !isIntermittent && (
                  <tr>
                    <td
                      data-label={t(
                        "pages.payments.paymentsTable.waitingWeekHeader"
                      )}
                    >
                      {t("pages.payments.paymentsTable.waitingWeekGeneric")}
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

export default withClaimDetail(Payments);
