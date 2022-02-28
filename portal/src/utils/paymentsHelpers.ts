import {
  BenefitsApplicationDocument,
  DocumentType,
  findDocumentsByTypes,
} from "../models/Document";
import { AbsencePeriod } from "src/models/AbsencePeriod";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import ClaimDetail from "src/models/ClaimDetail";
import LeaveReason from "src/models/LeaveReason";
import { Payment } from "src/models/Payment";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
import formatDate from "./formatDate";
import isBlank from "./isBlank";
import { isFeatureEnabled } from "src/services/featureFlags";

// TODO(PORTAL-1482): remove test cases for checkback dates
// remove dayjs and dayjsBusinessTime imports
dayjs.extend(dayjsBusinessTime);

export type PaymentStatusViewHelper = ReturnType<
  typeof paymentStatusViewHelper
>;

// Function to calculate and return the various pieces of data the status and payments pages need.
// Pending a restructure of the Payments and Status components it's going to be tempting to return
// things like 'showPaymentsTab' from here. Instead, create a new function like 'showPaymentsTab'.
export function paymentStatusViewHelper(
  claimDetail: ClaimDetail,
  documents: ApiResourceCollection<BenefitsApplicationDocument>,
  paymentList: Payment
) {
  const { absence_periods: _absencePeriods, has_paid_payments: _isPaid } =
    claimDetail;
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

  // info alerts, if any, should show if claim is pending, in review, or projected
  const hasPendingStatus = claimDetail.hasPendingStatus;
  const hasInReviewStatus = claimDetail?.hasInReviewStatus;
  const hasProjectedStatus = claimDetail?.hasProjectedStatus;

  // changes InfoAlert text
  const onlyHasNewBornBondingReason =
    _hasBondingReason && !_hasPregnancyReason && _hasNewBorn;
  const onlyHasPregnancyReason = _hasPregnancyReason && !_hasBondingReason;

  // only show waiting period row in the payments table if there is a waiting week on the claim detail
  // intermittent claims never have waiting weeks.
  const hasWaitingWeek =
    !isBlank(claimDetail.waitingWeek.startDate) && !isIntermittent;
  // 1. only show payments table if claimant has payments to show.
  // 2. changes intro text
  const payments = hasWaitingWeek
    ? paymentList.validPayments(claimDetail.waitingWeek.startDate)
    : paymentList.payments;
  const hasPayments = !!payments.length;

  const phaseTwoFeaturesEnabled = isFeatureEnabled(
    "claimantShowPaymentsPhaseTwo"
  );

  // changes intro text
  const isUnpaid = !_isPaid;

  // there is a 30 minute window between when the claim detail says the claim is approved
  // and the approval notice is available, we only want to display some content
  // if the user can also access the approval notice.
  const hasApprovalNotice = !!_approvalDate;

  // Check that either the status is "Approved" or we have the approval notice document
  const isApprovedAndHasApprovalDocument =
    hasApprovedStatus && hasApprovalNotice;

  // if payment is retroactive
  // and/or if the claim was approved within the first 14 days of the leave period
  // 1. changes intro text
  // 2. changes checkbackDate
  const isRetroactive = hasApprovalNotice
    ? _absencePeriods[_absencePeriods.length - 1]?.absence_period_end_date <
      _approvalDate
    : false;
  // case where claim is approved before 14th day but after claim has started
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
    // claim is approved after second week of leave start date (includes retroactive)
    if (isRetroactive || !isApprovedBeforeFourteenthDayOfClaim) {
      result = dayjs(_approvalDate).addBusinessDays(5);
    } else {
      // claim is approved before the second week of leave start date (includes before leave starts)
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
    hasInReviewStatus,
    hasProjectedStatus,
    isApprovedAndHasApprovalDocument,
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
    phaseTwoFeaturesEnabled,
  };
}

// Determine whether the payments tab should be shown
export function showPaymentsTab(helper: PaymentStatusViewHelper) {
  const {
    isApprovedAndHasApprovalDocument,
    phaseTwoFeaturesEnabled,
    hasPayments,
  } = helper;
  return (
    phaseTwoFeaturesEnabled && (isApprovedAndHasApprovalDocument || hasPayments)
  );
}

export function getInfoAlertContext(helper: PaymentStatusViewHelper) {
  const { onlyHasNewBornBondingReason, onlyHasPregnancyReason } = helper;
  if (onlyHasNewBornBondingReason) {
    return "bonding";
  }

  if (onlyHasPregnancyReason) {
    return "pregnancy";
  }

  return "";
}
