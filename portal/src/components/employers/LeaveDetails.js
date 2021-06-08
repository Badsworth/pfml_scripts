import Alert from "../Alert";
import ConditionalContent from "../../components/ConditionalContent";
import Details from "../Details";
import Document from "../../models/Document";
import EmployerClaim from "../../models/EmployerClaim";
import FormLabel from "../../components/FormLabel";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { Trans } from "react-i18next";
import download from "downloadjs";
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
        {absenceId}
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
          {documents.map((document) => (
            <HcpDocumentItem
              downloadDocument={downloadDocument}
              absenceId={absenceId}
              document={document}
              key={document.fineos_document_id}
            />
          ))}
        </ReviewRow>
      )}
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
            data-test="relationship-accurate-no"
          >
            <Alert
              state="warning"
              heading={t("components.employersLeaveDetails.inaccurateRelationshipAlertHeading")}
              headingSize="3"
              className="measure-5 margin-y-3"
            >
              {t("components.employersLeaveDetails.inaccurateRelationshipAlertLead")}
            </Alert>
            <FormLabel className="usa-label" htmlFor="comment" small>
              {t("components.employersLeaveDetails.commentHeading")}
            </FormLabel>
            <textarea
              className="usa-textarea margin-top-3"
              name="relationshipInaccurateReason"
              onChange={(event) =>
                onChangeRelationshipInaccurateReason(event.target.value)
              }
            />
          </ConditionalContent>

          <ConditionalContent
            visible={believeRelationshipAccurate === "Unknown"}
            data-test="relationship-accurate-unknown"
          >
            <Alert
              state="info"
              className="measure-5 margin-y-3"
            >
              {t("components.employersLeaveDetails.unknownRelationshipAlertLead")}
            </Alert>
          </ConditionalContent>
        </React.Fragment>
      )}
    </React.Fragment>
  );
};

LeaveDetails.propTypes = {
  believeRelationshipAccurate: PropTypes.oneOf(["Yes", "Unknown", "No"]),
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
  downloadDocument: PropTypes.func.isRequired,
  onChangeBelieveRelationshipAccurate: PropTypes.func,
  relationshipInaccurateReason: PropTypes.string,
  onChangeRelationshipInaccurateReason: PropTypes.func,
};

const HcpDocumentItem = (props) => {
  const { absenceId, document, downloadDocument } = props;
  const { t } = useTranslation();
  const documentName =
    document.name?.trim() ||
    t("components.employersLeaveDetails.healthCareProviderFormLink") ||
    document.document_type.trim();

  const handleClick = async (event) => {
    event.preventDefault();
    const documentData = await downloadDocument(absenceId, document);

    download(
      documentData,
      documentName,
      document.content_type || "application/pdf"
    );
  };

  return (
    <div>
      <a onClick={handleClick} href="">
        {documentName}
      </a>
    </div>
  );
};

HcpDocumentItem.propTypes = {
  absenceId: PropTypes.string.isRequired,
  document: PropTypes.instanceOf(Document).isRequired,
  downloadDocument: PropTypes.func.isRequired,
};

export default LeaveDetails;
