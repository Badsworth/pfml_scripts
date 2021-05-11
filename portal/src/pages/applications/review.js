import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../../models/PaymentPreference";
import BenefitsApplication, {
  EmploymentStatus,
  PhoneType,
  ReasonQualifier,
  ReducedScheduleLeavePeriod,
  RelationshipToCaregiver,
  WorkPattern,
  WorkPatternType,
} from "../../models/BenefitsApplication";
import Document, { DocumentType } from "../../models/Document";
import EmployerBenefit, {
  EmployerBenefitFrequency,
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import OtherIncome, {
  OtherIncomeFrequency,
  OtherIncomeType,
} from "../../models/OtherIncome";
import Step, { ClaimSteps } from "../../models/Step";
import { compact, get, isUndefined } from "lodash";

import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import Button from "../../components/Button";
import { DateTime } from "luxon";
import Heading from "../../components/Heading";
import HeadingPrefix from "../../components/HeadingPrefix";
import Lead from "../../components/Lead";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../../components/ReviewHeading";
import ReviewRow from "../../components/ReviewRow";
import Spinner from "../../components/Spinner";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import WeeklyTimeTable from "../../components/WeeklyTimeTable";
import claimantConfigs from "../../flows/claimant";
import convertMinutesToHours from "../../utils/convertMinutesToHours";
import findDocumentsByLeaveReason from "../../utils/findDocumentsByLeaveReason";
import findDocumentsByTypes from "../../utils/findDocumentsByTypes";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import getI18nContextForIntermittentFrequencyDuration from "../../utils/getI18nContextForIntermittentFrequencyDuration";
import hasDocumentsLoadError from "../../utils/hasDocumentsLoadError";
import { isFeatureEnabled } from "../../services/featureFlags";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";
import withClaimDocuments from "../../hoc/withClaimDocuments";

/**
 * Format an address onto a single line, or return undefined if the address
 * is empty.
 */
function formatAddress(address) {
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
export const Review = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim, documents, isLoadingDocuments } = props;

  const { appErrors } = appLogic;
  const hasLoadingDocumentsError = hasDocumentsLoadError(
    appErrors,
    claim.application_id
  );

  const certificationDocuments = findDocumentsByLeaveReason(documents, claim);
  const idDocuments = findDocumentsByTypes(documents, [
    DocumentType.identityVerification,
  ]);

  const payment_method = get(claim, "payment_preference.payment_method");
  const reasonQualifier = get(claim, "leave_details.reason_qualifier");
  const hasFutureChildDate = get(claim, "leave_details.has_future_child_date");
  const reducedLeavePeriod = new ReducedScheduleLeavePeriod(
    get(claim, "leave_details.reduced_schedule_leave_periods[0]")
  );
  const workPattern = new WorkPattern(get(claim, "work_pattern"));

  const steps = Step.createClaimStepsFromMachine(
    claimantConfigs,
    {
      claim: props.claim,
      showOtherLeaveStep: isFeatureEnabled("claimantShowOtherLeaveStep"),
    },
    null
  );

  const usePartOneReview = !claim.isSubmitted;

  const getStepEditHref = (name) => {
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

  const handleSubmit = useThrottledHandler(async () => {
    if (usePartOneReview) {
      await appLogic.benefitsApplications.submit(claim.application_id);
      return;
    }

    await appLogic.benefitsApplications.complete(claim.application_id);
  });

  const contentContext = usePartOneReview ? "part1" : "final";
  // Adjust heading levels depending on if there's a "Part 1" heading at the top of the page or not
  const reviewHeadingLevel = usePartOneReview ? "3" : "2";
  const reviewRowLevel = usePartOneReview ? "4" : "3";

  return (
    <div className="measure-6">
      <BackButton />

      <Title hidden>{t("pages.claimsReview.title")}</Title>

      <Heading className="margin-top-0" level="2" size="1">
        <HeadingPrefix>
          {t("pages.claimsReview.partHeadingPrefix", { number: 1 })}
        </HeadingPrefix>
        {t("pages.claimsReview.partHeading", {
          context: `${1}_${contentContext}`,
        })}
      </Heading>

      {!usePartOneReview && (
        <Lead>
          <Trans
            i18nKey="pages.claimsReview.partDescription"
            tOptions={{ context: "1" }}
            values={{ absence_id: claim.fineos_absence_id }}
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

      {get(claim, "occupation") && (
        <ReviewRow level={reviewRowLevel} label="Occupation">
          {get(claim, "occupation")}, {get(claim, "job_title")}
        </ReviewRow>
      )}

      {get(claim, "employment_status") === EmploymentStatus.employed && ( // only display this if the claimant is Employed
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employerFeinLabel")}
        >
          {get(claim, "employer_fein")}
        </ReviewRow>
      )}

      {get(claim, "employment_status") === EmploymentStatus.employed && ( // only display this if the claimant is Employed
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employerNotifiedLabel")}
        >
          {t("pages.claimsReview.employerNotifiedValue", {
            context: (!!get(
              claim,
              "leave_details.employer_notified"
            )).toString(),
            date: DateTime.fromISO(
              get(claim, "leave_details.employer_notification_date")
            ).toLocaleString(),
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

      {workPattern.work_pattern_type === WorkPatternType.fixed &&
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
          {!isUndefined(workPattern.minutesWorkedPerWeek) &&
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

      {claim.isMedicalLeave && (
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

      {claim.isReducedSchedule && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.reducedLeaveScheduleLabel")}
          // Only hide the border when we're rendering a WeeklyTimeTable
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
        get(claim, "has_other_incomes") !== null) && (
        <div data-test="other-leave">
          <ReviewHeading
            editHref={getStepEditHref(ClaimSteps.otherLeave)}
            editText={t("pages.claimsReview.editLink")}
            level={reviewHeadingLevel}
          >
            {t("pages.claimsReview.stepHeading", { context: "otherLeave" })}
          </ReviewHeading>

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
              get(claim, "other_incomes_awaiting_approval") === false &&
              t("pages.claimsReview.otherLeaveChoiceYes")}
            {get(claim, "has_other_incomes") === false &&
              get(claim, "other_incomes_awaiting_approval") === false &&
              t("pages.claimsReview.otherLeaveChoiceNo")}
            {get(claim, "has_other_incomes") === false &&
              get(claim, "other_incomes_awaiting_approval") === true &&
              t("pages.claimsReview.otherLeaveChoicePendingOtherIncomes")}
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
      ) : (
        <React.Fragment>
          <Heading level="2" size="1">
            <HeadingPrefix>
              {t("pages.claimsReview.partHeadingPrefix", { number: 2 })}
            </HeadingPrefix>
            {t("pages.claimsReview.partHeading", {
              context: "2",
            })}
          </Heading>

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
          <Heading level="2" size="1">
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
              <Spinner aria-valuetext={t("components.spinner.label")} />
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
                    data-test="certification-doc-count"
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

      <Button
        className="margin-top-3"
        onClick={handleSubmit}
        type="button"
        loading={handleSubmit.isThrottled}
        loadingMessage={t("pages.claimsReview.submitLoadingMessage")}
      >
        {t("pages.claimsReview.submitAction", {
          context: usePartOneReview ? "part1" : "final",
        })}
      </Button>
    </div>
  );
};

Review.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    benefitsApplications: PropTypes.object.isRequired,
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication),
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  isLoadingDocuments: PropTypes.bool,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

/*
 * Helper component for rendering an array of EmployerBenefit
 * objects.
 */
export const EmployerBenefitList = (props) => {
  const { t } = useTranslation();
  const { entries, reviewRowLevel } = props;

  return entries.map((entry, index) => {
    const label = t("pages.claimsReview.employerBenefitEntryLabel", {
      count: index + 1,
    });

    const type = t("pages.claimsReview.employerBenefitType", {
      context: findKeyByValue(EmployerBenefitType, entry.benefit_type),
    });

    const dates = formatDateRange(
      entry.benefit_start_date,
      entry.benefit_end_date
    );

    const amount = entry.benefit_amount_dollars
      ? t("pages.claimsReview.amountPerFrequency", {
          context: findKeyByValue(
            EmployerBenefitFrequency,
            entry.benefit_amount_frequency
          ),
          amount: entry.benefit_amount_dollars,
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
};

EmployerBenefitList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit)).isRequired,
  reviewRowLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
};

/*
 * Helper component for rendering an array of OtherIncome
 * objects.
 */
export const OtherIncomeList = (props) => {
  const { t } = useTranslation();
  const { entries, reviewRowLevel } = props;

  return entries.map((entry, index) => {
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

    const amount = entry.income_amount_dollars
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
};

OtherIncomeList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(OtherIncome)).isRequired,
  reviewRowLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
};

/*
 * Helper component for rendering a single other leave entry. This will
 * render a ReviewRow with the specified label, date string,
 * and an optional type string and amount string
 */
export const OtherLeaveEntry = (props) => {
  const { amount, dates, label, reviewRowLevel, type } = props;

  return (
    <ReviewRow level={reviewRowLevel} label={label}>
      {type && (
        <React.Fragment>
          {type}
          <br />
        </React.Fragment>
      )}
      {dates}
      <br />
      {amount}
    </ReviewRow>
  );
};

OtherLeaveEntry.propTypes = {
  amount: PropTypes.string,
  dates: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  reviewRowLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
  type: PropTypes.string,
};

export default withBenefitsApplication(withClaimDocuments(Review));
