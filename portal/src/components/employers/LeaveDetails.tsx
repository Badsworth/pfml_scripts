import Alert from "../Alert";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ClaimDocument from "../../models/ClaimDocument";
import ConditionalContent from "../ConditionalContent";
import DownloadableDocument from "../DownloadableDocument";
import EmployerClaim from "../../models/EmployerClaim";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { Trans } from "react-i18next";
import classnames from "classnames";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

/**
 * Display overview of a leave request
 * in the Leave Admin claim review page.
 */

const LeaveDetails = (props) => {
  const { t } = useTranslation();
  const {
    appErrors,
    believeRelationshipAccurate,
    claim: {
      fineos_absence_id: absenceId,
      isIntermittent,
      leave_details: { reason },
    },
    documents,
    downloadDocument,
    onChangeBelieveRelationshipAccurate,
    onChangeRelationshipInaccurateReason,
    relationshipInaccurateReason,
  } = props;

  const isCaringLeave = reason === LeaveReason.care;
  const isPregnancy = reason === LeaveReason.pregnancy;
  const errorMsg = appErrors.fieldErrorMessage(
    "relationship_inaccurate_reason"
  );

  const inaccurateReasonClasses = classnames("usa-form-group", {
    "usa-form-group--error": !!errorMsg,
  });

  const textAreaClasses = classnames("usa-textarea margin-top-3", {
    "usa-input--error": !!errorMsg,
  });

  const benefitsGuideLink = {
    [LeaveReason.care]: routes.external.massgov.benefitsGuide_aboutCaringLeave,
    [LeaveReason.bonding]:
      routes.external.massgov.benefitsGuide_aboutBondingLeave,
    [LeaveReason.medical]:
      routes.external.massgov.benefitsGuide_aboutMedicalLeave,
  };

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersLeaveDetails.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveTypeLabel")}
        data-test="leave-type"
      >
        {isPregnancy ? (
          t("components.employersLeaveDetails.leaveReasonValue", {
            context: findKeyByValue(LeaveReason, reason),
          })
        ) : (
          <a target="_blank" rel="noopener" href={benefitsGuideLink[reason]}>
            {t("components.employersLeaveDetails.leaveReasonValue", {
              context: findKeyByValue(LeaveReason, reason),
            })}
          </a>
        )}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.applicationIdLabel")}
      >
        {absenceId}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersLeaveDetails.leaveDurationLabel")}
      >
        {isIntermittent
          ? "—"
          : // @ts-expect-error ts-migrate(2554) FIXME: Expected 3 arguments, but got 2.
            formatDateRange(
              props.claim.leaveStartDate,
              props.claim.leaveEndDate
            )}
      </ReviewRow>
      {!!documents.length && (
        <ReviewRow
          level="3"
          label={t("components.employersLeaveDetails.documentationLabel")}
        >
          <Trans
            i18nKey="components.employersLeaveDetails.recordkeepingInstructions"
            components={{
              "mass-employer-role-link": (
                <a
                  href={routes.external.massgov.employersGuide}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
            tOptions={{ context: isCaringLeave ? "caringLeave" : null }}
          />
          <ul className="usa-list">
            {documents.map((document) => (
              <li key={document.fineos_document_id}>
                <DownloadableDocument
                  onDownloadClick={downloadDocument}
                  absenceId={absenceId}
                  document={document}
                  displayDocumentName={t(
                    "components.employersLeaveDetails.documentName"
                  )}
                />
              </li>
            ))}
          </ul>
        </ReviewRow>
      )}
      {isCaringLeave && (
        <React.Fragment>
          <InputChoiceGroup
            smallLabel
            name="believeRelationshipAccurate"
            onChange={(e) => {
              onChangeBelieveRelationshipAccurate(e.target.value);
            }}
            choices={[
              {
                checked: believeRelationshipAccurate === "Yes",
                label: t("components.employersLeaveDetails.choiceYes"),
                value: "Yes",
              },
              {
                checked: believeRelationshipAccurate === "Unknown",
                label: t("components.employersLeaveDetails.choiceUnknown"),
                value: "Unknown",
              },
              {
                checked: believeRelationshipAccurate === "No",
                label: t("components.employersLeaveDetails.choiceNo"),
                value: "No",
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
                    <a
                      target="_blank"
                      rel="noopener"
                      href={routes.external.massgov.caregiverRelationship}
                    />
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
            visible={believeRelationshipAccurate === "No"}
          >
            {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: string; state: string; heading: ... Remove this comment to see the full error message */}
            <Alert
              state="warning"
              heading={t(
                "components.employersLeaveDetails.inaccurateRelationshipAlertHeading"
              )}
              headingSize="3"
              className="measure-5 margin-y-3"
            >
              {t(
                "components.employersLeaveDetails.inaccurateRelationshipAlertLead"
              )}
            </Alert>
            <div className={inaccurateReasonClasses}>
              <FormLabel
                className="usa-label"
                inputId="relationshipInaccurateReason"
                small
                errorMsg={errorMsg}
              >
                {t("components.employersLeaveDetails.commentHeading")}
              </FormLabel>
              <textarea
                className={textAreaClasses}
                name="relationshipInaccurateReason"
                onChange={(event) =>
                  onChangeRelationshipInaccurateReason(event.target.value)
                }
                id="relationshipInaccurateReason"
              />
            </div>
          </ConditionalContent>

          <ConditionalContent
            visible={believeRelationshipAccurate === "Unknown"}
          >
            {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: string; state: string; className... Remove this comment to see the full error message */}
            <Alert state="info" className="measure-5 margin-y-3">
              {t(
                "components.employersLeaveDetails.unknownRelationshipAlertLead"
              )}
            </Alert>
          </ConditionalContent>
        </React.Fragment>
      )}
    </React.Fragment>
  );
};

LeaveDetails.propTypes = {
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  believeRelationshipAccurate: PropTypes.oneOf(["Yes", "Unknown", "No"]),
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(ClaimDocument)),
  downloadDocument: PropTypes.func.isRequired,
  onChangeBelieveRelationshipAccurate: PropTypes.func,
  relationshipInaccurateReason: PropTypes.string,
  onChangeRelationshipInaccurateReason: PropTypes.func,
};

export default LeaveDetails;
