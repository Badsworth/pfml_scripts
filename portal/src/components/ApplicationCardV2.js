import Document, { DocumentType } from "../models/Document";
import routeWithParams, {
  createRouteWithQuery,
} from "../utils/routeWithParams";

import BenefitsApplication from "../models/BenefitsApplication";
import ButtonLink from "../components/ButtonLink";
import DownloadableDocument from "../components/DownloadableDocument";
import Heading from "../components/Heading";
import Icon from "../components/Icon";
import LeaveReason from "../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import findDocumentsByTypes from "../utils/findDocumentsByTypes";
import findKeyByValue from "../utils/findKeyByValue";
import { useTranslation } from "../locales/i18n";
import withClaimDocuments from "../hoc/withClaimDocuments";

/**
 * Main header for the top of status cards
 */
const HeaderSection = ({ title }) => (
  <Heading className="margin-bottom-1 padding-2 padding-top-3" level="2">
    {title}
  </Heading>
);

HeaderSection.propTypes = {
  title: PropTypes.string.isRequired,
};

/**
 * Group together details for status cards
 */
const TitleAndDetailSectionItem = ({ details, title }) => (
  <div className="padding-2 padding-bottom-1 padding-top-0 margin-top-0">
    <p>{title}</p>
    <p className="margin-bottom-05 margin-top-05 text-bold">{details}</p>
  </div>
);

TitleAndDetailSectionItem.propTypes = {
  details: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
};

/**
 * Button section with top border and optional header text/section
 */
const ButtonSection = ({ buttonText, href, iconComponent = null }) => {
  return (
    <div className="border-top border-base-lighter padding-y-2 margin-2 margin-bottom-0">
      <ButtonLink
        className="display-flex flex-align-center flex-justify-center flex-column margin-right-0"
        href={href}
      >
        <div>{buttonText}</div>
        {iconComponent}
      </ButtonLink>
    </div>
  );
};

ButtonSection.propTypes = {
  buttonText: PropTypes.string.isRequired,
  href: PropTypes.string.isRequired,
  iconComponent: PropTypes.object,
};

ButtonSection.defaultProps = {
  iconComponent: null,
};

/**
 * Section to view notices and upload documents
 */
const ManageDocumentSection = ({ claim }) => {
  const { t } = useTranslation();
  const { fineos_absence_id: absence_case_id } = claim;

  const viewNoticesLink = createRouteWithQuery(
    "/applications/status/#view_notices",
    { absence_case_id }
  );

  const uploadDocumentsLink = createRouteWithQuery(
    "/applications/status/#upload_documents",
    { absence_case_id }
  );

  return (
    <div className="border-top border-base-lighter margin-2 margin-top-0 padding-bottom-1">
      <Heading className="padding-y-3" level="3">
        {t("components.applicationCardV2.manageApplicationDocuments")}
      </Heading>
      <ButtonLink
        className="display-block margin-bottom-3"
        href={viewNoticesLink}
        variation="unstyled"
      >
        {t("components.applicationCardV2.viewNotices")}
      </ButtonLink>

      <ButtonLink
        className="display-block margin-bottom-2"
        href={uploadDocumentsLink}
        variation="unstyled"
      >
        {t("components.applicationCardV2.uploadDocuments")}
      </ButtonLink>
    </div>
  );
};

ManageDocumentSection.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

/**
 * Section to view notices and upload documents
 */
const LegalNoticeSection = ({ appLogic, claim, documents }) => {
  const isSubmitted = claim.status === "Submitted";
  const hasDocuments = Boolean(documents?.length);
  const { t } = useTranslation();

  /**
   * If application is not submitted or has
   * no documents, don't display section
   */
  if (!isSubmitted || !hasDocuments) return null;

  const legalNotices = findDocumentsByTypes(documents, [
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
  ]);

  const legalNoticeList = legalNotices.map((document) => (
    <li
      className="grid-row flex-row flex-justify-start flex-align-start margin-bottom-1 text-primary"
      key={document.fineos_document_id}
    >
      <Icon
        className="margin-right-1"
        fill="currentColor"
        name="file_present"
        size={3}
      />
      <div>
        <DownloadableDocument
          className="margin-left-2"
          document={document}
          onDownloadClick={appLogic.documents.download}
          showCreatedAt
        />
      </div>
    </li>
  ));

  return (
    <div className="margin-2 margin-top-0 padding-bottom-1">
      <Heading level="3">{t("components.applicationCardV2.notice")}</Heading>
      <p className="padding-bottom-2 margin-top-05" style={{ maxWidth: 385 }}>
        {t("components.applicationCardV2.noticeOnClickDetails")}
      </p>
      <ul className="add-list-reset">{legalNoticeList}</ul>
    </div>
  );
};

LegalNoticeSection.defaultProps = {
  documents: [],
};

LegalNoticeSection.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
  }).isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
};

/**
 * Status card for claim.status != "Completed" (In Progress)
 */
const InProgressStatusCard = (props) => {
  const { claim, number } = props;
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <HeaderSection
        title={t("components.applicationCardV2.heading", {
          number,
        })}
      />
      <TitleAndDetailSectionItem
        title={t("components.applicationCardV2.employerEIN")}
        details={claim.employer_fein}
      />
      <LegalNoticeSection {...props} />
      <ButtonSection
        buttonText={t("components.applicationCardV2.continueApplication")}
        href={routeWithParams("applications.checklist", {
          claim_id: claim.application_id,
        })}
      />
    </React.Fragment>
  );
};

InProgressStatusCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  /**  The 1-based index of the application card */
  number: PropTypes.number.isRequired,
};

/**
 * Status card for claim.status = "Completed"
 */
const CompletedStatusCard = ({ claim }) => {
  const { t } = useTranslation();

  const leaveReasonText = t("components.applicationCardV2.leaveReasonValue", {
    context: findKeyByValue(LeaveReason, claim.leave_details?.reason),
  });

  const iconComponent = (
    <Icon
      className="position-absolute flex-align-self-end margin-right-neg-105"
      fill="white"
      name="arrow_forward"
      size={3}
    />
  );

  return (
    <React.Fragment>
      <HeaderSection title={leaveReasonText} />
      <TitleAndDetailSectionItem
        title={t("components.applicationCardV2.applicationID")}
        details={claim.fineos_absence_id}
      />
      <TitleAndDetailSectionItem
        title={t("components.applicationCardV2.employerEIN")}
        details={claim.employer_fein}
      />

      <ButtonSection
        buttonText={t(
          "components.applicationCardV2.viewStatusUpdatesAndDetails"
        )}
        href={routeWithParams("applications.status", {
          absence_case_id: claim.fineos_absence_id,
        })}
        iconComponent={iconComponent}
      />
      <ManageDocumentSection claim={claim} />
    </React.Fragment>
  );
};

CompletedStatusCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 */
export const ApplicationCardV2 = (props) => {
  const {
    claim: { status },
  } = props;

  const StatusCard = () => {
    switch (status) {
      case "Completed":
        return <CompletedStatusCard {...props} />;

      default:
        return <InProgressStatusCard {...props} />;
    }
  };

  return (
    <div className="maxw-mobile-lg">
      <aside className="border-top-1 border-primary" />
      <article className="border-x border-bottom border-base-lighter">
        <StatusCard />
      </article>
    </div>
  );
};

ApplicationCardV2.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withClaimDocuments(ApplicationCardV2);
