import Alert from "../Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../Details";
import EmployerClaim from "../../models/EmployerClaim";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

/**
 * Display overview of a leave request
 * in the Leave Admin claim review page.
 */

const LeaveDetails = (props) => {
  const { t } = useTranslation();
  const {
    claim: {
      fineos_absence_id,
      isIntermittent,
      leave_details: { reason },
    },
    believeRelationshipAccurate,
    onChangeBelieveRelationshipAccurate,
    onChangeRelationshipInaccurateReason,
    relationshipInaccurateReason,
  } = props;

  const isCaringLeave = reason === LeaveReason.care;
  const shouldShowCaringLeave = isFeatureEnabled("showCaringLeaveType");

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersLeaveDetails.header")}
      </ReviewHeading>
      {props.claim.isBondingLeave && (
        <div className="measure-6">
          <Details
            label={t(
              "components.employersLeaveDetails.bondingRegsReviewDetailsLabel"
            )}
          >
            <p>
              <Trans
                i18nKey="components.employersLeaveDetails.bondingRegsReviewDetailsSummary"
                components={{
                  "emergency-bonding-regs-employer-link": (
                    <a
                      target="_blank"
                      rel="noopener"
                      href={
                        routes.external.massgov
                          .emergencyBondingRegulationsEmployer
                      }
                    />
                  ),
                }}
              />
            </p>
          </Details>
        </div>
      )}
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveTypeLabel")}
      >
        {t("components.employersLeaveDetails.leaveReasonValue", {
          context: findKeyByValue(LeaveReason, reason),
        })}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.applicationIdLabel")}
      >
        {fineos_absence_id}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveDurationLabel")}
      >
        {isIntermittent
          ? "—"
          : formatDateRange(
              props.claim.leaveStartDate,
              props.claim.leaveEndDate
            )}
      </ReviewRow>
      {shouldShowCaringLeave && isCaringLeave && (
        <React.Fragment>
          <InputChoiceGroup
            smallLabel
            name="believeRelationshipAccurate"
            onChange={(e) => {
              onChangeBelieveRelationshipAccurate(e.target.value);
            }}
            choices={[
              {
                checked: believeRelationshipAccurate === "yes",
                label: t("components.employersLeaveDetails.choiceYes"),
                value: "yes",
              },
              {
                checked: believeRelationshipAccurate === "unknown",
                label: t("components.employersLeaveDetails.choiceUnknown"),
                value: "unknown",
              },
              {
                checked: believeRelationshipAccurate === "no",
                label: t("components.employersLeaveDetails.choiceNo"),
                value: "no",
              },
            ]}
            label={
              <ReviewHeading level="2">
                {t(
                  "components.employersLeaveDetails.familyMemberRelationshipLabel"
                )}
              </ReviewHeading>
            }
            hint={
              <Trans
                i18nKey="components.employersLeaveDetails.familyMemberRelationshipHint"
                components={{
                  "eligible-relationship-link": (
                    <a href={routes.external.caregiverRelationship} />
                  ),
                }}
              />
            }
            type="radio"
          />

          <ConditionalContent
            getField={() => relationshipInaccurateReason}
            clearField={() => onChangeRelationshipInaccurateReason("")}
            updateFields={(event) =>
              onChangeRelationshipInaccurateReason(event.target.value)
            }
            visible={believeRelationshipAccurate === "no"}
          >
            <Alert
              state="warning"
              heading={t("components.employersLeaveDetails.warningHeading")}
              headingSize="3"
              className="measure-5 margin-bottom-3 margin-top-3"
            >
              {t("components.employersLeaveDetails.warningLead")}
            </Alert>
            <FormLabel className="usa-label" htmlFor="comment" small>
              {t("components.employersLeaveDetails.commentHeading")}
            </FormLabel>
            <textarea
              className="usa-textarea margin-top-3"
              name="comment"
              onChange={(event) =>
                onChangeRelationshipInaccurateReason(event.target.value)
              }
            />
          </ConditionalContent>
        </React.Fragment>
      )}
    </React.Fragment>
  );
};

LeaveDetails.propTypes = {
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
  believeRelationshipAccurate: PropTypes.oneOf(["yes", "unknown", "no", ""]),
  onChangeBelieveRelationshipAccurate: PropTypes.func,
  relationshipInaccurateReason: PropTypes.string,
  onChangeRelationshipInaccurateReason: PropTypes.func,
};

export default LeaveDetails;
