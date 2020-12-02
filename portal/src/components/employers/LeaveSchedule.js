import Document, { DocumentType } from "../../models/Document";
import React, { useEffect } from "react";
import DocumentCollection from "../../models/DocumentCollection";
import EmployerClaim from "../../models/EmployerClaim";
import IntermittentLeaveSchedule from "./IntermittentLeaveSchedule";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import Table from "../Table";
import download from "downloadjs";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";

/**
 * Display leave periods by leave type
 * in the Leave Admin claim review page.
 */

const LeaveSchedule = ({ appLogic, claim }) => {
  const { t } = useTranslation();
  const {
    employers: { documents, loadDocuments },
  } = appLogic;
  const {
    isContinuous,
    isIntermittent,
    isReducedSchedule,
    fineos_absence_id: absenceId,
    leave_details: { intermittent_leave_periods },
  } = claim;

  useEffect(() => {
    if (!documents) {
      loadDocuments(absenceId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents, absenceId]);

  // only HCP forms should be shown
  const medicalDocuments = (documents?.items || []).filter(
    (document) => document.document_type === DocumentType.medicalCertification
  );

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("pages.employersClaimsReview.leaveSchedule.header")}
      </ReviewHeading>
      <Table className="width-full">
        <caption className="text-normal">
          <p>{t("pages.employersClaimsReview.leaveSchedule.caption")}</p>
        </caption>
        <thead>
          <tr>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_dateRange"
              )}
            </th>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_leaveFrequency"
              )}
            </th>
            <th scope="col">
              {t(
                "pages.employersClaimsReview.leaveSchedule.tableHeader_details"
              )}
            </th>
          </tr>
        </thead>
        <tbody>
          {isContinuous && (
            <tr>
              <th scope="row">
                {formatDateRange(
                  get(
                    claim,
                    "leave_details.continuous_leave_periods[0].start_date"
                  ),
                  get(
                    claim,
                    "leave_details.continuous_leave_periods[0].end_date"
                  )
                )}
              </th>
              <td colSpan="2">
                {t("pages.employersClaimsReview.leaveSchedule.type_continuous")}
              </td>
            </tr>
          )}
          {isReducedSchedule && (
            <tr>
              <th scope="row">
                {formatDateRange(
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].start_date"
                  ),
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].end_date"
                  )
                )}
              </th>
              <td>
                {t(
                  "pages.employersClaimsReview.leaveSchedule.type_reducedSchedule"
                )}
              </td>
              <td>
                {/* TODO (EMPLOYER-364): Remove hardcoded number of hours */}
                {/* TODO (CP-1074): Update hours/day */}
                {t(
                  "pages.employersClaimsReview.leaveSchedule.reducedHoursPerWeek",
                  {
                    numOfHours: 10,
                  }
                )}
              </td>
            </tr>
          )}
          {isIntermittent && (
            <IntermittentLeaveSchedule
              intermittentLeavePeriods={intermittent_leave_periods}
            />
          )}
        </tbody>
      </Table>
      {!!medicalDocuments.length && (
        <ReviewRow
          level="3"
          label={t("pages.employersClaimsReview.documentationLabel")}
        >
          {medicalDocuments.map((document) => (
            <HcpDocumentItem
              appLogic={appLogic}
              absenceId={absenceId}
              document={document}
              key={document.fineos_document_id}
            />
          ))}
        </ReviewRow>
      )}
    </React.Fragment>
  );
};

LeaveSchedule.propTypes = {
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      documents: PropTypes.instanceOf(DocumentCollection),
      loadDocuments: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
};

const HcpDocumentItem = (props) => {
  const { absenceId, appLogic, document } = props;
  const { t } = useTranslation();

  const documentName =
    document.name?.trim() ||
    t("pages.employersClaimsReview.leaveSchedule.healthCareProviderFormLink") ||
    document.document_type.trim();

  const handleClick = async (event) => {
    event.preventDefault();
    const documentData = await appLogic.employers.downloadDocument(
      absenceId,
      document
    );

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
  appLogic: PropTypes.shape({
    employers: PropTypes.shape({
      downloadDocument: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  document: PropTypes.instanceOf(Document).isRequired,
};

export default LeaveSchedule;
