import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../models/PaymentPreference";
import {
  DocumentType,
  findDocumentsByTypes,
  getLeaveCertificationDocs,
} from "../../models/Document";
import EmployerBenefit, {
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import {
  EmploymentStatus,
  Gender,
  PhoneType,
  ReasonQualifier,
  ReducedScheduleLeavePeriod,
  RelationshipToCaregiver,
  WorkPattern,
  WorkPatternType,
} from "../../models/BenefitsApplication";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../models/OtherIncome";
import PreviousLeave, { PreviousLeaveReason } from "../../models/PreviousLeave";
import React, { useEffect, useState } from "react";
import Step, { ClaimSteps } from "../../models/Step";
import { compact, get } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import withClaimDocuments, {
  WithClaimDocumentsProps,
} from "../../hoc/withClaimDocuments";

import Address from "../../models/Address";
import Alert from "../../components/core/Alert";
import BackButton from "../../components/BackButton";
import Heading from "../../components/core/Heading";
import HeadingPrefix from "../../components/core/HeadingPrefix";
import Lead from "../../components/core/Lead";
import LeaveReason from "../../models/LeaveReason";
import ReviewHeading from "../../components/ReviewHeading";
import ReviewRow from "../../components/ReviewRow";
import Spinner from "../../components/core/Spinner";
import ThrottledButton from "../../components/ThrottledButton";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import WeeklyTimeTable from "../../components/WeeklyTimeTable";
import claimantConfigs from "../../flows/claimant";
import convertMinutesToHours from "../../utils/convertMinutesToHours";
import dayjs from "dayjs";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDate from "../../utils/formatDate";
import formatDateRange from "../../utils/formatDateRange";
import getI18nContextForIntermittentFrequencyDuration from "../../utils/getI18nContextForIntermittentFrequencyDuration";
import getMissingRequiredFields from "../../utils/getMissingRequiredFields";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import isBlank from "../../utils/isBlank";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "src/routes";
import tracker from "../../services/tracker";
import { useTranslation } from "../../locales/i18n";

/**
 * Format an address onto a single line, or return undefined if the address
 * is empty.
 */
function formatAddress(address: Partial<Address> | null) {
  let formatted = compact([
    get(address, "line_1"),
    get(address, "line_2"),
    get(address, "city"),
    get(address, "state"),
  ]).join(", ");

  const zip = get(address, "zip");
  if (zip) formatted += " " + zip;

  return formatted;
}

/**
 * Application review page, allowing a user to review the info
 * they've entered before they submit it.
 */
export const Review = (
  props: WithClaimDocumentsProps & WithBenefitsApplicationProps
) => {
  const { t } = useTranslation();
  const { appLogic, claim, documents, isLoadingDocuments } = props;
  const { loadCrossedBenefitYears, getCrossedBenefitYear } =
    appLogic.benefitYears;

  const employeeId = get(claim, "employee_id");
  const startDate = String(get(claim, "leaveStartDate"));
  const endDate = String(get(claim, "leaveEndDate"));
  const submissionWindow = dayjs().add(60, "day").format("YYYY-MM-DD");

  useEffect(() => {
    if (employeeId != null) {
      loadCrossedBenefitYears(employeeId, startDate, endDate);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeId, startDate, endDate]);
  const crossedBenefitYear = getCrossedBenefitYear();
  const canSubmitBoth =
    crossedBenefitYear !== null &&
    crossedBenefitYear.benefit_year_end_date <= submissionWindow;

  const { errors, clearRequiredFieldErrors } = appLogic;
  const hasLoadingDocumentsError = hasDocumentsLoadError(
    errors,
    claim.application_id
  );

  const certificationDocuments = getLeaveCertificationDocs(documents);
  const idDocuments = findDocumentsByTypes(documents, [
    DocumentType.identityVerification,
  ]);

  const payment_method = get(claim, "payment_preference.payment_method");
  const reasonQualifier = get(claim, "leave_details.reason_qualifier");
  const hasFutureChildDate = get(claim, "leave_details.has_future_child_date");
  const reducedLeavePeriod = new ReducedScheduleLeavePeriod(
    get(claim, "leave_details.reduced_schedule_leave_periods[0]")
  );
  const workPattern = new WorkPattern(get(claim, "work_pattern") || {});
  const gender = get(claim, "gender");
  const isEmployed =
    get(claim, "employment_status") === EmploymentStatus.employed;

  const steps = Step.createClaimStepsFromMachine(claimantConfigs, {
    claim: props.claim,
  });

  const usePartOneReview = !claim.isSubmitted;

  const getStepEditHref = (name: string) => {
    const step = steps.find((s) => s.name === name);

    if (step && step.editable) {
      return appLogic.portalFlow.getNextPageRoute(
        step.name,
        { claim },
        {
          claim_id: claim.application_id,
        }
      );
    }
  };

  const handleSubmit = async () => {
    setShowNewFieldError(false);
    if (usePartOneReview) {
      await appLogic.benefitsApplications.submit(claim.application_id);
      return;
    }

    await appLogic.benefitsApplications.complete(claim.application_id);
  };

  // Adjust heading levels depending on if there's a "Part 1" heading at the top of the page or not
  const reviewHeadingLevel = usePartOneReview ? "3" : "2";
  const reviewRowLevel = usePartOneReview ? "4" : "3";

  // If there are any required field errors then display a custom error message and clear the required
  // field errors so they don't render in the default error boundary. This can happen if a user reached
  // the review page just before we a deployed a new question or page, or if the user somehow skipped  a
  // page with required fields.
  const [showNewFieldError, setShowNewFieldError] = useState(false);
  useEffect(() => {
    const missingFields = getMissingRequiredFields(errors);
    if (missingFields.length) {
      tracker.trackEvent("Missing required fields", {
        missingFields: JSON.stringify(missingFields),
      });

      clearRequiredFieldErrors();
      if (!showNewFieldError) {
        // Display a custom error alert with a link back to the checklist
        setShowNewFieldError(true);
      }
    }
  }, [
    errors,
    showNewFieldError,
    setShowNewFieldError,
    clearRequiredFieldErrors,
  ]);

  return (
    <div className="measure-6">
      {showNewFieldError && (
        <Alert className="margin-bottom-3">
          <Trans
            i18nKey="pages.claimsReview.missingRequiredFieldError"
            components={{
              "checklist-link": (
                <a
                  href={appLogic.portalFlow.getNextPageRoute(
                    "CHECKLIST",
                    { claim },
                    {
                      claim_id: claim.application_id,
                    }
                  )}
                />
              ),
            }}
          />
        </Alert>
      )}
      <BackButton />

      {usePartOneReview && (
        <Title hidden>{t("pages.claimsReview.title_part1")}</Title>
      )}
      {!usePartOneReview && (
        <Title marginBottom="6">{t("pages.claimsReview.title_final")}</Title>
      )}

      <Heading className="margin-top-0" level="2">
        <HeadingPrefix>
          {t("pages.claimsReview.partHeadingPrefix", { number: 1 })}
        </HeadingPrefix>
        {t("pages.claimsReview.partHeading_1")}
      </Heading>

      {!usePartOneReview && (
        <Lead>
          <Trans
            i18nKey="pages.claimsReview.partDescription"
            values={{ absence_id: claim.fineos_absence_id, step: 1 }}
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        </Lead>
      )}

      {/* EMPLOYEE IDENTITY */}
      <ReviewHeading
        editHref={getStepEditHref(ClaimSteps.verifyId)}
        editText={t("pages.claimsReview.editLink")}
        level={reviewHeadingLevel}
      >
        {t("pages.claimsReview.stepHeading", { context: "verifyId" })}
      </ReviewHeading>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.userNameLabel")}
      >
        {[
          get(claim, "first_name"),
          get(claim, "middle_name"),
          get(claim, "last_name"),
        ].join(" ")}
      </ReviewRow>

      {gender && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.userGenderLabel")}
        >
          {t("pages.claimsReview.genderValue", {
            context: findKeyByValue(Gender, gender),
          })}
        </ReviewRow>
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.phoneLabel")}
      >
        {t("pages.claimsReview.phoneType", {
          context: findKeyByValue(PhoneType, get(claim, "phone.phone_type")),
        })}
        <br />
        {get(claim, "phone.phone_number")}
      </ReviewRow>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.residentialAddressLabel")}
      >
        {formatAddress(get(claim, "residential_address"))}
      </ReviewRow>

      {claim.has_mailing_address && (
        <ReviewRow
          label={t("pages.claimsReview.mailingAddressLabel")}
          level={reviewRowLevel}
        >
          {formatAddress(get(claim, "mailing_address"))}
        </ReviewRow>
      )}

      {claim.has_state_id && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.userStateIdLabel")}
        >
          {claim.mass_id}
        </ReviewRow>
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.userTaxIdLabel")}
      >
        {get(claim, "tax_identifier")}
      </ReviewRow>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.userDateOfBirthLabel")}
      >
        {formatDateRange(get(claim, "date_of_birth"))}
      </ReviewRow>

      {/* EMPLOYMENT INFO */}
      <ReviewHeading
        editHref={getStepEditHref(ClaimSteps.employerInformation)}
        editText={t("pages.claimsReview.editLink")}
        level={reviewHeadingLevel}
      >
        {t("pages.claimsReview.stepHeading", {
          context: "employerInformation",
        })}
      </ReviewHeading>
      {/* TODO (CP-1281): Show employment status when Portal supports other employment statuses */}
      {isFeatureEnabled("claimantShowEmploymentStatus") &&
        get(claim, "employment_status") && (
          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.employmentStatusLabel")}
          >
            {t("pages.claimsReview.employmentStatusValue", {
              context: findKeyByValue(
                EmploymentStatus,
                get(claim, "employment_status")
              ),
            })}
          </ReviewRow>
        )}

      {isEmployed && ( // only display this if the claimant is Employed
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employerFeinLabel")}
        >
          {get(claim, "employer_fein")}
        </ReviewRow>
      )}

      {get(claim, "organization_unit") && ( // only displays this if the claimant is Employed
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employeeOrganizationUnit")}
        >
          {get(claim, "organization_unit.name")}
        </ReviewRow>
      )}

      {isEmployed && ( // only display this if the claimant is Employed
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employerNotifiedLabel")}
        >
          {t("pages.claimsReview.employerNotifiedValue", {
            context: (!!get(
              claim,
              "leave_details.employer_notified"
            )).toString(),
            date: formatDate(
              get(claim, "leave_details.employer_notification_date")
            ).short(),
          })}
        </ReviewRow>
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.workPatternTypeLabel")}
      >
        {t("pages.claimsReview.workPatternTypeValue", {
          context: findKeyByValue(
            WorkPatternType,
            get(claim, "work_pattern.work_pattern_type")
          ),
        })}
      </ReviewRow>

      {workPattern.work_pattern_days &&
        workPattern.work_pattern_type === WorkPatternType.fixed &&
        workPattern.minutesWorkedPerWeek !== null && (
          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.workPatternDaysFixedLabel")}
            noBorder
          >
            <WeeklyTimeTable days={workPattern.work_pattern_days} />
          </ReviewRow>
        )}

      {workPattern.work_pattern_type === WorkPatternType.variable && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.workPatternDaysVariableLabel")}
        >
          {!isBlank(workPattern.minutesWorkedPerWeek) &&
            t("pages.claimsReview.workPatternVariableTime", {
              context:
                convertMinutesToHours(workPattern.minutesWorkedPerWeek)
                  .minutes === 0
                  ? "noMinutes"
                  : null,
              ...convertMinutesToHours(workPattern.minutesWorkedPerWeek),
            })}
        </ReviewRow>
      )}

      {/* LEAVE DETAILS */}
      <ReviewHeading
        editHref={getStepEditHref(ClaimSteps.leaveDetails)}
        editText={t("pages.claimsReview.editLink")}
        level={reviewHeadingLevel}
      >
        {t("pages.claimsReview.stepHeading", { context: "leaveDetails" })}
      </ReviewHeading>

      {crossedBenefitYear !== null && canSubmitBoth && (
        <React.Fragment>
          <Alert
            state="info"
            heading={t("shared.crossedBenefitYear.header")}
            autoWidth
          >
            <Trans
              i18nKey="shared.crossedBenefitYear.submittingBoth"
              components={{
                b: <b />,
                ul: <ul className="usa-list" />,
                li: <li />,
                "benefits-amount-link": (
                  <a
                    href={
                      routes.external.massgov.benefitsGuide_weeklyBenefitAmounts
                    }
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                "terms-to-know-link": (
                  <a
                    href={routes.external.massgov.importantTermsToKnow}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                "waiting-week-link": (
                  <a
                    href={routes.external.massgov.sevenDayWaitingPeriodInfo}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
              }}
              values={{
                benefitYearStartDate: formatDate(
                  crossedBenefitYear.benefit_year_start_date
                ).short(),
                benefitYearEndDate: formatDate(
                  crossedBenefitYear.benefit_year_end_date
                ).short(),
                newBenefitYearStartDate: formatDate(
                  dayjs(crossedBenefitYear.benefit_year_end_date)
                    .add(1, "day")
                    .format("YYYY-MM-DD")
                ).short(),
                leaveStartDate: formatDate(startDate).short(),
                leaveEndDate: formatDate(endDate).short(),
              }}
            />
          </Alert>
          <p></p>
        </React.Fragment>
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.leaveReasonLabel")}
      >
        {t("pages.claimsReview.leaveReasonValue", {
          context: findKeyByValue(
            LeaveReason,
            get(claim, "leave_details.reason")
          ),
        })}
      </ReviewRow>

      {claim.isMedicalOrPregnancyLeave && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.pregnancyOrRecentBirthLabel")}
        >
          {t("pages.claimsReview.pregnancyOrRecentBirth", {
            context: get(claim, "leave_details.pregnant_or_recent_birth")
              ? "yes"
              : "no",
          })}
        </ReviewRow>
      )}

      {claim.isBondingLeave && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.familyLeaveTypeLabel")}
        >
          {t("pages.claimsReview.familyLeaveTypeValue", {
            context: findKeyByValue(ReasonQualifier, reasonQualifier),
          })}
        </ReviewRow>
      )}

      {claim.isBondingLeave && reasonQualifier === ReasonQualifier.newBorn && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.childBirthDateLabel")}
        >
          {formatDateRange(get(claim, "leave_details.child_birth_date"))}
        </ReviewRow>
      )}

      {claim.isBondingLeave &&
        [ReasonQualifier.adoption, ReasonQualifier.fosterCare].includes(
          reasonQualifier
        ) && (
          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.childPlacementDateLabel")}
          >
            {formatDateRange(get(claim, "leave_details.child_placement_date"))}
          </ReviewRow>
        )}

      {claim.isCaringLeave && (
        <React.Fragment>
          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.familyMemberRelationshipLabel")}
          >
            {t("pages.claimsReview.familyMemberRelationship", {
              context: findKeyByValue(
                RelationshipToCaregiver,
                get(
                  claim,
                  "leave_details.caring_leave_metadata.relationship_to_caregiver"
                )
              ),
            })}
          </ReviewRow>
          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.familyMemberNameLabel")}
          >
            {[
              get(
                claim,
                "leave_details.caring_leave_metadata.family_member_first_name"
              ),
              get(
                claim,
                "leave_details.caring_leave_metadata.family_member_middle_name"
              ),
              get(
                claim,
                "leave_details.caring_leave_metadata.family_member_last_name"
              ),
            ].join(" ")}
          </ReviewRow>
          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.familyMemberDateOfBirthLabel")}
          >
            {formatDateRange(
              get(
                claim,
                "leave_details.caring_leave_metadata.family_member_date_of_birth"
              )
            )}
          </ReviewRow>
        </React.Fragment>
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.leavePeriodLabel", {
          context: "continuous",
        })}
      >
        {claim.isContinuous
          ? claim.continuousLeaveDateRange()
          : t("pages.claimsReview.leavePeriodNotSelected")}
      </ReviewRow>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.leavePeriodLabel", {
          context: "reduced",
        })}
      >
        {claim.isReducedSchedule
          ? claim.reducedLeaveDateRange()
          : t("pages.claimsReview.leavePeriodNotSelected")}
      </ReviewRow>
      {/* Only hide the border when we're rendering a WeeklyTimeTable */}
      {claim.isReducedSchedule && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.reducedLeaveScheduleLabel")}
          noBorder={workPattern.work_pattern_type === WorkPatternType.fixed}
        >
          {workPattern.work_pattern_type === WorkPatternType.fixed && (
            <WeeklyTimeTable
              className="margin-bottom-0"
              days={reducedLeavePeriod.days}
            />
          )}
          {workPattern.work_pattern_type === WorkPatternType.variable &&
            t("pages.claimsReview.reducedLeaveScheduleWeeklyTotal", {
              context:
                convertMinutesToHours(reducedLeavePeriod.totalMinutesOff)
                  .minutes === 0
                  ? "noMinutes"
                  : null,
              ...convertMinutesToHours(reducedLeavePeriod.totalMinutesOff),
            })}
        </ReviewRow>
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.leavePeriodLabel", {
          context: "intermittent",
        })}
      >
        {claim.isIntermittent
          ? claim.intermittentLeaveDateRange()
          : t("pages.claimsReview.leavePeriodNotSelected")}
      </ReviewRow>

      {claim.isIntermittent && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.intermittentFrequencyDurationLabel")}
        >
          <Trans
            i18nKey="pages.claimsReview.intermittentFrequencyDuration"
            tOptions={{
              context: getI18nContextForIntermittentFrequencyDuration(
                get(claim, "leave_details.intermittent_leave_periods[0]")
              ),
              duration: get(
                claim,
                "leave_details.intermittent_leave_periods[0].duration"
              ),
              frequency: get(
                claim,
                "leave_details.intermittent_leave_periods[0].frequency"
              ),
            }}
          />
        </ReviewRow>
      )}

      {/* OTHER LEAVE */}
      {/* Conditionally showing this section since it was added after launch, so some claims may not have this section yet. */}
      {(get(claim, "has_employer_benefits") !== null ||
        get(claim, "has_other_incomes") !== null ||
        get(claim, "has_previous_leaves_same_reason") !== null ||
        get(claim, "has_previous_leaves_other_reason") !== null ||
        get(claim, "has_concurrent_leave") !== null) && (
        <div>
          <ReviewHeading
            editHref={getStepEditHref(ClaimSteps.otherLeave)}
            editText={t("pages.claimsReview.editLink")}
            level={reviewHeadingLevel}
          >
            {t("pages.claimsReview.stepHeading", { context: "otherLeave" })}
          </ReviewHeading>
          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.previousLeaveHasPreviousLeavesLabel")}
          >
            {(get(claim, "has_previous_leaves_same_reason") ||
              get(claim, "has_previous_leaves_other_reason")) === true
              ? t("pages.claimsReview.otherLeaveChoiceYes")
              : t("pages.claimsReview.otherLeaveChoiceNo")}
          </ReviewRow>
          <PreviousLeaveList
            entries={get(claim, "previous_leaves_same_reason")}
            type="sameReason"
            startIndex={0}
            reviewRowLevel={reviewRowLevel}
          />
          <PreviousLeaveList
            entries={get(claim, "previous_leaves_other_reason")}
            type="otherReason"
            startIndex={get(claim, "previous_leaves_same_reason.length", 0)}
            reviewRowLevel={reviewRowLevel}
          />

          <ReviewRow
            level={reviewRowLevel}
            label={t(
              "pages.claimsReview.concurrentLeaveHasConcurrentLeaveLabel"
            )}
          >
            {get(claim, "has_concurrent_leave") === true
              ? t("pages.claimsReview.otherLeaveChoiceYes")
              : t("pages.claimsReview.otherLeaveChoiceNo")}
          </ReviewRow>
          {get(claim, "concurrent_leave") && (
            <ReviewRow
              level={reviewRowLevel}
              label={t("pages.claimsReview.concurrentLeaveLabel")}
            >
              <p className="text-base-darker margin-top-1">
                {formatDateRange(
                  get(claim, "concurrent_leave.leave_start_date"),
                  get(claim, "concurrent_leave.leave_end_date")
                )}
              </p>
              <ul className="usa-list margin-top-1">
                <li>
                  {t("pages.claimsReview.isForCurrentEmployer", {
                    context: String(
                      get(claim, "concurrent_leave.is_for_current_employer")
                    ),
                  })}
                </li>
              </ul>
            </ReviewRow>
          )}

          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.employerBenefitLabel")}
          >
            {get(claim, "has_employer_benefits") === true
              ? t("pages.claimsReview.otherLeaveChoiceYes")
              : t("pages.claimsReview.otherLeaveChoiceNo")}
          </ReviewRow>

          {get(claim, "has_employer_benefits") && (
            <EmployerBenefitList
              entries={get(claim, "employer_benefits")}
              reviewRowLevel={reviewRowLevel}
            />
          )}

          <ReviewRow
            level={reviewRowLevel}
            label={t("pages.claimsReview.otherIncomeLabel")}
          >
            {get(claim, "has_other_incomes") === true &&
              t("pages.claimsReview.otherLeaveChoiceYes")}
            {get(claim, "has_other_incomes") === false &&
              t("pages.claimsReview.otherLeaveChoiceNo")}
          </ReviewRow>

          {get(claim, "has_other_incomes") && (
            <OtherIncomeList
              entries={get(claim, "other_incomes")}
              reviewRowLevel={reviewRowLevel}
            />
          )}
        </div>
      )}

      {usePartOneReview ? (
        <React.Fragment>
          {crossedBenefitYear !== null && !canSubmitBoth ? (
            <Alert
              state="info"
              heading={t("shared.crossedBenefitYear.header")}
              autoWidth
            >
              <Trans
                i18nKey="pages.claimsReview.crossedBenefitYearSubmittingOne"
                components={{
                  b: <b />,
                  ul: <ul className="usa-list" />,
                  li: <li />,
                  "terms-to-know-link": (
                    <a
                      href={routes.external.massgov.importantTermsToKnow}
                      rel="noopener noreferrer"
                      target="_blank"
                    />
                  ),
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
                values={{
                  benefitYearStartDate: formatDate(
                    crossedBenefitYear.benefit_year_start_date
                  ).short(),
                  benefitYearEndDate: formatDate(
                    crossedBenefitYear.benefit_year_end_date
                  ).short(),
                  newBenefitYearStartDate: formatDate(
                    dayjs(crossedBenefitYear.benefit_year_end_date)
                      .add(1, "day")
                      .format("YYYY-MM-DD")
                  ).short(),
                  leaveStartDate: formatDate(startDate).short(),
                  leaveEndDate: formatDate(endDate).short(),
                  applicationSubmissionDate: formatDate(
                    dayjs(crossedBenefitYear.benefit_year_end_date)
                      .add(1, "day")
                      .subtract(60, "day")
                      .format("YYYY-MM-DD")
                  ).short(),
                }}
              />
            </Alert>
          ) : (
            <div className="margin-top-6 margin-bottom-2">
              <Trans
                i18nKey="pages.claimsReview.partOneNextSteps"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
            </div>
          )}
        </React.Fragment>
      ) : (
        <React.Fragment>
          <Heading level="2">
            <HeadingPrefix>
              {t("pages.claimsReview.partHeadingPrefix", { number: 2 })}
            </HeadingPrefix>
            {t("pages.claimsReview.partHeading", {
              context: "2",
            })}
          </Heading>
          <Lead>
            <Trans
              i18nKey="pages.claimsReview.partDescription"
              values={{ absence_id: claim.fineos_absence_id, step: 2 }}
              components={{
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
              }}
            />
          </Lead>

          {/* PAYMENT METHOD */}
          <ReviewHeading level={reviewHeadingLevel}>
            {t("pages.claimsReview.stepHeading", { context: "payment" })}
          </ReviewHeading>

          {payment_method && (
            <ReviewRow
              label={t("pages.claimsReview.paymentMethodLabel")}
              level={reviewRowLevel}
            >
              {t("pages.claimsReview.paymentMethodValue", {
                context: findKeyByValue(
                  PaymentPreferenceMethod,
                  payment_method
                ),
              })}
            </ReviewRow>
          )}
          {payment_method === PaymentPreferenceMethod.ach && (
            <React.Fragment>
              <ReviewRow
                label={t("pages.claimsReview.paymentRoutingNumLabel")}
                level={reviewRowLevel}
              >
                {get(claim, "payment_preference.routing_number")}
              </ReviewRow>
              <ReviewRow
                label={t("pages.claimsReview.paymentAccountNumLabel")}
                level={reviewRowLevel}
              >
                {get(claim, "payment_preference.account_number")}
              </ReviewRow>
              <ReviewRow
                label={t("pages.claimsReview.achTypeLabel")}
                level={reviewRowLevel}
              >
                {t("pages.claimsReview.achType", {
                  context: findKeyByValue(
                    BankAccountType,
                    get(claim, "payment_preference.bank_account_type")
                  ),
                })}
              </ReviewRow>
            </React.Fragment>
          )}
          {typeof claim.is_withholding_tax === "boolean" && (
            <React.Fragment>
              <ReviewHeading level={reviewHeadingLevel}>
                {t("pages.claimsReview.stepHeading", { context: "tax" })}
              </ReviewHeading>
              <ReviewRow
                label={t("pages.claimsReview.taxLabel")}
                level={reviewRowLevel}
              >
                {claim.is_withholding_tax === true
                  ? t("pages.claimsReview.taxYesWithhold")
                  : t("pages.claimsReview.taxNoWithhold")}
              </ReviewRow>
            </React.Fragment>
          )}
          <Heading level="2">
            <HeadingPrefix>
              {t("pages.claimsReview.partHeadingPrefix", { number: 3 })}
            </HeadingPrefix>
            {t("pages.claimsReview.partHeading", {
              context: "3",
            })}
          </Heading>
          {hasLoadingDocumentsError && (
            <Alert className="margin-bottom-3" noIcon>
              <Trans
                i18nKey="pages.claimsReview.documentsLoadError"
                components={{
                  "contact-center-phone-link": (
                    <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                  ),
                }}
              />
            </Alert>
          )}
          {isLoadingDocuments && !hasLoadingDocumentsError && (
            <div className="margin-top-8 text-center">
              <Spinner aria-label={t("components.spinner.label")} />
            </div>
          )}
          {!isLoadingDocuments && !hasLoadingDocumentsError && (
            <React.Fragment>
              <ReviewHeading
                editHref={getStepEditHref(ClaimSteps.uploadId)}
                editText={t("pages.claimsReview.editLink")}
                level={reviewHeadingLevel}
              >
                {t("pages.claimsReview.stepHeading", { context: "uploadId" })}
              </ReviewHeading>
              <ReviewRow
                label={t("pages.claimsReview.numberOfFilesLabel")}
                level={reviewRowLevel}
              >
                {idDocuments.length}
              </ReviewRow>
              {!hasFutureChildDate && (
                <React.Fragment>
                  <ReviewHeading
                    editHref={getStepEditHref(ClaimSteps.uploadCertification)}
                    editText={t("pages.claimsReview.editLink")}
                    level={reviewHeadingLevel}
                  >
                    {t("pages.claimsReview.stepHeading", {
                      context: "uploadCertification",
                    })}
                  </ReviewHeading>
                  <ReviewRow
                    label={t("pages.claimsReview.numberOfFilesLabel")}
                    level={reviewRowLevel}
                  >
                    {certificationDocuments.length}
                  </ReviewRow>
                </React.Fragment>
              )}
            </React.Fragment>
          )}
          <Trans i18nKey="pages.claimsReview.employerWarning" />
        </React.Fragment>
      )}

      <ThrottledButton
        className="margin-top-3"
        onClick={handleSubmit}
        type="button"
        loadingMessage={t("pages.claimsReview.submitLoadingMessage")}
      >
        {t("pages.claimsReview.submitAction", {
          context: usePartOneReview ? "part1" : "final",
        })}
      </ThrottledButton>
    </div>
  );
};

interface PreviousLeaveListProps {
  type: "sameReason" | "otherReason";
  entries: PreviousLeave[];
  /** start index for previous leave label */
  startIndex: number;
  reviewRowLevel: "2" | "3" | "4" | "5" | "6";
}

export const PreviousLeaveList = (props: PreviousLeaveListProps) => {
  const { t } = useTranslation();
  if (!props.entries.length) return null;

  const rows = props.entries.map((entry, index) => (
    <ReviewRow
      level={props.reviewRowLevel}
      key={`${props.type}-${index}`}
      label={t("pages.claimsReview.previousLeaveEntryLabel", {
        count: props.startIndex + index + 1,
      })}
    >
      <p className="text-base-darker margin-top-1">
        {formatDateRange(entry.leave_start_date, entry.leave_end_date)}
      </p>
      <ul className="usa-list margin-top-1">
        <li>
          {t("pages.claimsReview.previousLeaveType", { context: props.type })}
        </li>
        <li>
          {t("pages.claimsReview.isForCurrentEmployer", {
            context: String(get(entry, "is_for_current_employer")),
          })}
        </li>
        {props.type === "otherReason" && (
          <li>
            {t("pages.claimsReview.previousLeaveReason", {
              context: findKeyByValue(
                PreviousLeaveReason,
                get(entry, "leave_reason")
              ),
            })}
          </li>
        )}
        <li>
          {t("pages.claimsReview.previousLeaveWorkedPerWeekMinutesLabel")}
          {t("pages.claimsReview.previousLeaveWorkedPerWeekMinutes", {
            context:
              convertMinutesToHours(entry.worked_per_week_minutes).minutes === 0
                ? "noMinutes"
                : null,
            ...convertMinutesToHours(entry.worked_per_week_minutes),
          })}
        </li>
        <li>
          {t("pages.claimsReview.previousLeaveLeaveMinutesLabel")}
          {t("pages.claimsReview.previousLeaveLeaveMinutes", {
            context:
              convertMinutesToHours(entry.leave_minutes).minutes === 0
                ? "noMinutes"
                : null,
            ...convertMinutesToHours(entry.leave_minutes),
          })}
        </li>
      </ul>
    </ReviewRow>
  ));

  return <React.Fragment>{rows}</React.Fragment>;
};

interface EmployerBenefitListProps {
  entries: EmployerBenefit[];
  reviewRowLevel: "2" | "3" | "4" | "5" | "6";
}

/*
 * Helper component for rendering an array of EmployerBenefit
 * objects.
 */
export const EmployerBenefitList = (props: EmployerBenefitListProps) => {
  const { t } = useTranslation();
  const { entries, reviewRowLevel } = props;

  const rows = entries.map((entry, index) => {
    const label = t("pages.claimsReview.employerBenefitEntryLabel", {
      count: index + 1,
    });

    const type = t("pages.claimsReview.employerBenefitType", {
      context: findKeyByValue(EmployerBenefitType, entry.benefit_type),
    });

    let dates;

    if (entry.is_full_salary_continuous) {
      dates = formatDateRange(entry.benefit_start_date, entry.benefit_end_date);
    }

    return (
      <OtherLeaveEntry
        key={index}
        label={label}
        type={type}
        dates={dates}
        amount={null}
        reviewRowLevel={reviewRowLevel}
      />
    );
  });

  return <React.Fragment>{rows}</React.Fragment>;
};

interface OtherIncomeListProps {
  entries: OtherIncome[];
  reviewRowLevel: "2" | "3" | "4" | "5" | "6";
}

/*
 * Helper component for rendering an array of OtherIncome
 * objects.
 */
export const OtherIncomeList = (props: OtherIncomeListProps) => {
  const { t } = useTranslation();
  const { entries, reviewRowLevel } = props;

  const rows = entries.map((entry, index) => {
    const label = t("pages.claimsReview.otherIncomeEntryLabel", {
      count: index + 1,
    });

    const type = t("pages.claimsReview.otherIncomeType", {
      context: findKeyByValue(OtherIncomeType, entry.income_type),
    });

    const dates = formatDateRange(
      entry.income_start_date,
      entry.income_end_date
    );

    const amount = !isBlank(entry.income_amount_dollars)
      ? t("pages.claimsReview.amountPerFrequency", {
          context: findKeyByValue(
            OtherIncomeFrequency,
            entry.income_amount_frequency
          ),
          amount: entry.income_amount_dollars,
        })
      : null;

    return (
      <OtherLeaveEntry
        key={index}
        label={label}
        type={type}
        dates={dates}
        amount={amount}
        reviewRowLevel={reviewRowLevel}
      />
    );
  });

  return <React.Fragment>{rows}</React.Fragment>;
};

interface OtherLeaveEntryProps {
  amount?: string | null;
  dates?: string;
  label: string;
  reviewRowLevel: "2" | "3" | "4" | "5" | "6";
  type?: string;
}

/*
 * Helper component for rendering a single other leave entry. This will
 * render a ReviewRow with the specified label, date string,
 * and an optional type string and amount string
 */
export const OtherLeaveEntry = (props: OtherLeaveEntryProps) => {
  const { amount, dates, label, reviewRowLevel, type } = props;

  return (
    <ReviewRow level={reviewRowLevel} label={label}>
      <p className="text-base-darker margin-top-1">{dates}</p>
      <ul className="usa-list margin-top-1">
        {type && <li>{type}</li>}
        {amount && <li>{amount}</li>}
      </ul>
    </ReviewRow>
  );
};

export default withBenefitsApplication(withClaimDocuments(Review));
