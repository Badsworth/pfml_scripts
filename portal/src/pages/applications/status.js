import Document, { DocumentType } from "../../models/Document";
import React, { useEffect, useState } from "react";
import { has, map } from "lodash";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import ClaimDetail from "../../models/ClaimDetail";
import Heading from "../../components/Heading";
import LeaveReason from "../../models/LeaveReason";
import LegalNoticeList from "../../components/LegalNoticeList.js";
import PropTypes from "prop-types";
import Tag from "../../components/Tag";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDate from "../../utils/formatDate";
import { handleError } from "../../api/BaseApi";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
// TODO (CP-2461): remove once page is integrated with API
const TEST_DOC = [
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.approvalNotice,
    fineos_document_id: "fineos-id-4",
    name: "legal notice",
  }),
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.denialNotice,
    fineos_document_id: "fineos-id-5",
    name: "legal notice 2",
  }),
];

const TEST_CLAIM = new ClaimDetail({
  absence_periods: [
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-06-01",
      absence_period_end_date: "2021-06-08",
      request_decision: "Approved",
      fineos_leave_request_id: "PL-14432-0000002026",
      reason: LeaveReason.medical,
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-07-01",
      absence_period_end_date: "2021-07-08",
      request_decision: "Pending",
      fineos_leave_request_id: "PL-14432-0000002326",
      reason: LeaveReason.medical,
    },
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Denied",
      fineos_leave_request_id: "PL-14434-0000002026",
      reason: LeaveReason.bonding,
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Withdrawn",
      fineos_leave_request_id: "PL-14434-0000002326",
      reason: LeaveReason.bonding,
    },
  ],
});

export const Status = ({
  appLogic,
  docList = TEST_DOC,
  absenceDetails = TEST_CLAIM.absencePeriodsByReason,
}) => {
  const { t } = useTranslation();
  const { portalFlow } = appLogic;

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowStatusPage")) {
      portalFlow.goTo(routes.applications.index);
    }
  }, [portalFlow]);

  const [documents, setDocuments] = useState(docList);
  useEffect(() => {
    function loadDocuments() {
      try {
        const loadedDocuments = { items: docList };
        setDocuments(loadedDocuments.items);
      } catch (error) {
        handleError(error);
      }
    }
    loadDocuments();
  }, [docList]);

  if (appLogic.appErrors.items.length) return null;

  const ViewYourNotices = () => {
    return documents.length ? (
      <div className="border-bottom border-base-lighter padding-bottom-2">
        <Heading className="margin-bottom-1" level="2" id="view_notices">
          {t("pages.claimsStatus.viewNoticesHeading")}
        </Heading>
        <LegalNoticeList
          documents={documents}
          onDownloadClick={appLogic.documents.download}
        />
      </div>
    ) : null;
  };

  const getInfoAlertContext = (absenceDetails) => {
    const hasBondingReason = has(absenceDetails, LeaveReason.bonding);
    const hasPregnancyReason = has(absenceDetails, LeaveReason.pregnancy);

    if (hasBondingReason && !hasPregnancyReason) {
      return "bonding";
    }

    if (hasPregnancyReason && !hasBondingReason) {
      return "pregnancy";
    }

    return "";
  };
  const infoAlertContext = getInfoAlertContext(absenceDetails);

  const containerClassName = "border-top border-base-lighter padding-top-2";

  return (
    <React.Fragment>
      {!!infoAlertContext && (
        <Alert
          className="margin-bottom-3"
          data-test="info-alert"
          heading={t("pages.claimsStatus.infoAlertHeading", {
            context: infoAlertContext,
          })}
          headingLevel="2"
          headingSize="4"
          noIcon
          state="info"
        >
          <Trans
            i18nKey="pages.claimsStatus.infoAlertBody"
            tOptions={{ context: infoAlertContext }}
            components={{
              "about-bonding-leave-link": (
                <a
                  href={routes.external.massgov.benefitsGuide_aboutBondingLeave}
                  target="_blank"
                  rel="noreferrer noopener"
                />
              ),
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
          />
        </Alert>
      )}
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <Title weight="normal" small>
          {t("pages.claimsStatus.applicationDetails")}
        </Title>

        {/* Heading section */}

        <Heading level="2" size="1">
          {/* // TODO (CP-2449): placeholder */}
          Leave Reason
        </Heading>
        <div className="display-flex border-base-lighter margin-bottom-3 bg-base-lightest padding-2">
          <div className="padding-right-10">
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.applicationID")}
            </Heading>
            {/* // TODO (CP-2449): placeholder */}
            <p className="text-bold">Fineos-Absence-ID</p>
          </div>
          <div>
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.employerEIN")}
            </Heading>
            {/* // TODO (CP-2449): placeholder */}
            <p className="text-bold">123456789</p>
          </div>
        </div>

        <LeaveDetails absenceDetails={absenceDetails} />
        <ViewYourNotices />

        {/* Upload documents section */}
        <div className={containerClassName}>
          <Heading level="2">
            {t("pages.claimsStatus.uploadDocumentsHeading")}
          </Heading>
          <Heading level="3">
            {t("pages.claimsStatus.infoRequestsHeading")}
          </Heading>
          <p>{t("pages.claimsStatus.infoRequestsBody")}</p>
          {/* // TODO (CP-2457): update claim_id to claim.application_id */}
          <ButtonLink
            className="measure-6 margin-bottom-3"
            href={routeWithParams("applications.uploadDocsOptions", {
              claim_id: "65184a9e-f938-40b6-b0f6-25f416a4c113",
            })}
          >
            {t("pages.claimsStatus.uploadDocumentsButton")}
          </ButtonLink>
        </div>

        {/* Manage applications section */}
        <div className={containerClassName}>
          <Heading level="2">
            {t("pages.claimsStatus.manageApplicationHeading")}
          </Heading>
          <Heading level="3">
            {t("pages.claimsStatus.makeChangesHeading")}
          </Heading>
          <Trans
            i18nKey="pages.claimsStatus.makeChangesBody"
            components={{
              "contact-center-phone-link": (
                <a
                  href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`}
                />
              ),
            }}
          />
          <Heading level="3">
            {t("pages.claimsStatus.reportOtherBenefitsHeading")}
          </Heading>
          <Trans
            i18nKey="pages.claimsStatus.reportOtherBenefitsBody"
            components={{
              "contact-center-phone-link": (
                <a
                  href={`tel:${t("shared.contactCenterPhoneNumberNoBreak")}`}
                />
              ),
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </div>
      </div>
    </React.Fragment>
  );
};

Status.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  // TODO (CP-2461): remove once page is integrated with API
  docList: PropTypes.array,
  absenceDetails: PropTypes.object,
};

export default Status;

export const StatusTagMap = {
  Approved: "success",
  Denied: "error",
  Pending: "pending",
  Withdrawn: "inactive",
};

export const LeaveDetails = ({ absenceDetails = {} }) => {
  const { t } = useTranslation();
  return map(absenceDetails, (absenceItem, absenceItemName) => (
    <div
      key={absenceItemName}
      className="border-bottom border-base-lighter margin-bottom-2 padding-bottom-2"
    >
      <Heading level="2">
        {t("pages.claimsStatus.leaveReasonValue", {
          context: findKeyByValue(LeaveReason, absenceItemName),
        })}
      </Heading>
      {absenceItem.length
        ? absenceItem.map(
            ({
              period_type,
              absence_period_start_date,
              absence_period_end_date,
              request_decision,
              fineos_leave_request_id,
            }) => (
              <div key={fineos_leave_request_id} className="margin-top-2">
                <Heading className="margin-bottom-1" level="3">
                  {t("pages.claimsStatus.leavePeriodLabel", {
                    context: period_type.toLowerCase(),
                  })}
                </Heading>
                <p>
                  {`From ${formatDate(
                    absence_period_start_date
                  ).full()} to ${formatDate(absence_period_end_date).full()}`}
                </p>
                <Tag
                  paddingSm
                  label={request_decision}
                  state={StatusTagMap[request_decision]}
                />
                <Trans
                  i18nKey="pages.claimsStatus.leaveStatusMessage"
                  tOptions={{ context: request_decision }}
                  components={{
                    "application-link": (
                      <a href={routes.applications.getReady} />
                    ),
                    "notice-link": <a href="#view_notices" />,
                    "request-appeal-link": (
                      <a
                        href={routes.external.massgov.requestAnAppealForPFML}
                      />
                    ),
                  }}
                />
              </div>
            )
          )
        : null}
    </div>
  ));
};
