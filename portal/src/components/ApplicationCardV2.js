// @ts-nocheck: https://lwd.atlassian.net/browse/PORTAL-427
import routeWithParams, {
  createRouteWithQuery,
} from "../utils/routeWithParams";

import BenefitsApplication from "../models/BenefitsApplication";
import ButtonLink from "./ButtonLink";
import Document from "../models/Document";
import Heading from "./Heading";
import Icon from "./Icon";
import LeaveReason from "../models/LeaveReason";
import LegalNoticeList from "./LegalNoticeList";
import PropTypes from "prop-types";
import React from "react";
import Spinner from "./Spinner";
import ThrottledButton from "./ThrottledButton";
import findKeyByValue from "../utils/findKeyByValue";
import getLegalNotices from "../utils/getLegalNotices";
import hasDocumentsLoadError from "../utils/hasDocumentsLoadError";
import { useTranslation } from "../locales/i18n";
import withClaimDocuments from "../hoc/withClaimDocuments";

/**
 * Assists with page navigation, displays errors on the
 * current page rather than redirecting and showing the
 * error on a new page.
 */
const navigateToPage = async (claim, appLogic, href) => {
  const { fineos_absence_id } = claim;
  const claimDetail = await appLogic.claims.loadClaimDetail(fineos_absence_id);
  const isValidClaim = claimDetail?.fineos_absence_id === fineos_absence_id;

  // navigate to page if claim loads w/o errors
  if (isValidClaim) appLogic.portalFlow.goTo(href);
};

/**
 * Main header for the top of status cards
 */
const HeaderSection = ({ title }) => (
  <Heading
    className="margin-bottom-1 padding-2 padding-top-3"
    level="3"
    size="2"
  >
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
 * Section to view notices and upload documents
 */
const ManageDocumentSection = ({ appLogic, claim }) => {
  const { t } = useTranslation();
  const { fineos_absence_id: absence_case_id } = claim;

  const onClickHandler = async (href) => {
    await navigateToPage(claim, appLogic, href);
  };

  const viewNoticesLink = createRouteWithQuery(
    "/applications/status/",
    { absence_case_id },
    "view_notices"
  );

  const uploadDocumentsLink = createRouteWithQuery(
    "/applications/status/",
    { absence_case_id },
    "upload_documents"
  );

  return (
    <div className="border-top border-base-lighter margin-2 margin-top-0 padding-bottom-1">
      <Heading className="padding-y-3" level="4">
        {t("components.applicationCardV2.otherActions")}
      </Heading>
      <ThrottledButton
        className="display-block margin-bottom-3"
        onClick={() => onClickHandler(viewNoticesLink)}
        variation="unstyled"
      >
        {t("components.applicationCardV2.viewNotices")}
      </ThrottledButton>

      <ThrottledButton
        className="display-block margin-bottom-2"
        onClick={() => onClickHandler(uploadDocumentsLink)}
        variation="unstyled"
      >
        {t("components.applicationCardV2.respondToRequest")}
      </ThrottledButton>
    </div>
  );
};

ManageDocumentSection.propTypes = {
  appLogic: PropTypes.shape({
    claims: PropTypes.shape({
      isLoadingClaimDetail: PropTypes.bool,
      loadClaimDetail: PropTypes.func.isRequired,
    }).isRequired,
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

/**
 * Section to view legal notices for in-progress applications
 */
const LegalNoticeSection = (props) => {
  const { t } = useTranslation();
  const isSubmitted = props.claim.status === "Submitted";
  const legalNotices = getLegalNotices(props.documents);
  const shouldShowSpinner =
    props.isLoadingDocuments &&
    !hasDocumentsLoadError(
      props.appLogic.appErrors,
      props.claim.application_id
    );

  /**
   * If application is not submitted,
   * don't display section
   */
  if (!isSubmitted) return null;

  // check for spinner before documents length, since length is 0 while loading.
  if (shouldShowSpinner) {
    return (
      <div className="text-center">
        <Spinner
          small
          aria-valuetext={t("components.applicationCardV2.loadingLabel")}
        />
      </div>
    );
  }

  if (!legalNotices.length) return null;

  return (
    <div
      className="margin-2 margin-top-0 padding-bottom-1"
      style={{ maxWidth: 385 }}
    >
      <Heading level="3">
        {t("components.applicationCardV2.viewNotices")}
      </Heading>
      <LegalNoticeList
        onDownloadClick={props.appLogic.documents.download}
        {...props}
      />
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
  isLoadingDocuments: PropTypes.bool.isRequired,
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
      {claim.employer_fein && (
        <TitleAndDetailSectionItem
          title={t("components.applicationCardV2.employerEIN")}
          details={claim.employer_fein}
        />
      )}
      <LegalNoticeSection {...props} />
      <div className="border-top border-base-lighter padding-y-2 margin-2 margin-bottom-0">
        <ButtonLink
          className="display-flex flex-align-center flex-justify-center flex-column margin-right-0"
          href={routeWithParams("applications.checklist", {
            claim_id: claim.application_id,
          })}
        >
          <div>{t("components.applicationCardV2.continueApplication")}</div>
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

InProgressStatusCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  isLoadingDocuments: PropTypes.bool.isRequired,
  /**  The 1-based index of the application card */
  number: PropTypes.number.isRequired,
};

/**
 * Status card for claim.status = "Completed"
 */
const CompletedStatusCard = ({ appLogic, claim }) => {
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

  const statusPage = routeWithParams("applications.status", {
    absence_case_id: claim.fineos_absence_id,
  });

  const onClickHandler = async () => {
    await navigateToPage(claim, appLogic, statusPage);
  };

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

      <div className="border-top border-base-lighter padding-y-2 margin-2 margin-bottom-0">
        <ThrottledButton
          className="width-full display-flex flex-align-center flex-justify-center flex-column margin-right-0"
          onClick={onClickHandler}
        >
          {t("components.applicationCardV2.viewStatusUpdatesAndDetails")}
          {iconComponent}
        </ThrottledButton>
      </div>
      <ManageDocumentSection appLogic={appLogic} claim={claim} />
    </React.Fragment>
  );
};

CompletedStatusCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  appLogic: PropTypes.shape({
    claims: PropTypes.shape({
      isLoadingClaimDetail: PropTypes.bool,
      loadClaimDetail: PropTypes.func.isRequired,
    }).isRequired,
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
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

  return (
    <div className="maxw-mobile-lg margin-bottom-3">
      <aside className="border-top-1 border-primary" />
      <article className="border-x border-bottom border-base-lighter">
        {status === "Completed" ? (
          <CompletedStatusCard {...props} />
        ) : (
          <InProgressStatusCard {...props} />
        )}
      </article>
    </div>
  );
};

ApplicationCardV2.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    claims: PropTypes.shape({
      isLoadingClaimDetail: PropTypes.bool,
      loadClaimDetail: PropTypes.func.isRequired,
    }).isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  isLoadingDocuments: PropTypes.bool.isRequired,
};

export default withClaimDocuments(ApplicationCardV2);
