import React, { useEffect } from "react";
import Document from "../../models/Document";
import DocumentCollection from "../../models/DocumentCollection";
import EmployerClaim from "../../models/EmployerClaim";
import IntermittentLeaveSchedule from "./IntermittentLeaveSchedule";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import Table from "../Table";
import { Trans } from "react-i18next";
import download from "downloadjs";
import findDocumentsByLeaveReason from "../../utils/findDocumentsByLeaveReason";
import formatDateRange from "../../utils/formatDateRange";
import { get } from "lodash";
import routes from "../../routes";
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
  const allDocuments = documents ? documents.items : [];
  const certificationDocuments = findDocumentsByLeaveReason(
    allDocuments,
    get(claim, "leave_details.reason")
  );

  const buildContext = () => {
    const hasDocuments = !!certificationDocuments.length;
    if (isIntermittent && hasDocuments) return "intermittentWithDocuments";
    if (!isIntermittent && hasDocuments) return "documents";
  };

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersLeaveSchedule.header")}
      </ReviewHeading>
      <Table className="width-full">
        <caption>
          <p className="text-normal">
            <Trans
              i18nKey="components.employersLeaveSchedule.caption"
              tOptions={{
                context: buildContext() || "",
              }}
            />
          </p>
          <p>{t("components.employersLeaveSchedule.tableName")}</p>
        </caption>
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersLeaveSchedule.dateRangeLabel")}
            </th>
            <th scope="col">
              {t("components.employersLeaveSchedule.leaveFrequencyLabel")}
            </th>
            <th scope="col">
              {t("components.employersLeaveSchedule.detailsLabel")}
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
                {t(
                  "components.employersLeaveSchedule.claimDurationType_continuous"
                )}
              </td>
            </tr>
          )}
          {isReducedSchedule && (
            <tr>
              <th scope="row">
                {/* TODO (EMPLOYER-655): Update reduced leave details */}
                {/* {formatDateRange(
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].start_date"
                  ),
                  get(
                    claim,
                    "leave_details.reduced_schedule_leave_periods[0].end_date"
                  )
                )} */}
              </th>
              <td>
                {t(
                  "components.employersLeaveSchedule.claimDurationType_reducedSchedule"
                )}
              </td>
              <td>
                {/* TODO (CP-1074): Update hours/day */}
                {/* TODO (EMPLOYER-655): Update reduced leave details */}
                <Trans
                  i18nKey="components.employersLeaveSchedule.downloadAttachments"
                  components={{
                    "contact-center-phone-link": (
                      <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                    ),
                  }}
                />
                {/* {t(
                  "components.employersLeaveSchedule.reducedHoursPerWeek",
                  {
                    numOfHours: 10,
                  }
                )} */}
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
      {!!certificationDocuments.length && (
        <ReviewRow
          level="3"
          label={t("components.employersLeaveSchedule.documentationLabel")}
        >
          <Trans
            i18nKey="components.employersLeaveSchedule.recordkeepingInstructions"
            components={{
              "mass-employer-role-link": (
                <a
                  href={routes.external.massgov.employersGuide}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
          />
          <p>
            {certificationDocuments.map((document) => (
              <HcpDocumentItem
                appLogic={appLogic}
                absenceId={absenceId}
                document={document}
                key={document.fineos_document_id}
              />
            ))}
          </p>
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
    t("components.employersLeaveSchedule.healthCareProviderFormLink") ||
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
