import routeWithParams, {
  createRouteWithQuery,
} from "../utils/routeWithParams";

import BenefitsApplication from "../models/BenefitsApplication";
import ButtonLink from "../components/ButtonLink";
import Document from "../models/Document";
import Heading from "../components/Heading";
import Icon from "../components/Icon";
import LeaveReason from "../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import findKeyByValue from "../utils/findKeyByValue";
import { useTranslation } from "../locales/i18n";

// REUSABLE STATUS CARD SECTIONS
/**
 * Main header for the top of status cards
 * @param {string} title - Title of the status card
 * @returns {ReactElement}
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
const TitleAndDetailSection = ({ details, title }) => (
  <div className="padding-2 padding-bottom-1 padding-top-0 margin-top-0">
    <Heading level="4" size="6">
      {title}
    </Heading>
    <Heading className="margin-bottom-1 margin-top-1" level="4">
      {details}
    </Heading>
  </div>
);

TitleAndDetailSection.propTypes = {
  details: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
};

/**
 * Button section with top border and optional header text/section
 */
const GroupButtonSection = ({ buttonText, href, iconComponent = null }) => {
  return (
    <div className="border-top border-base-lighter padding-2 margin-1 margin-bottom-0">
      <ButtonLink
        className="display-flex flex-align-center flex-justify-center flex-column"
        href={href}
      >
        <div>{buttonText}</div>
        {iconComponent}
      </ButtonLink>
    </div>
  );
};

GroupButtonSection.propTypes = {
  buttonText: PropTypes.string.isRequired,
  href: PropTypes.string.isRequired,
  iconComponent: PropTypes.object,
};

GroupButtonSection.defaultProps = {
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
    <div className="border-top border-base-lighter padding-2 padding-top-0 margin-1 margin-top-0">
      <Heading className="padding-bottom-3 padding-top-3" level="4">
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

// STATUS CARDS
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
      <TitleAndDetailSection
        title={t("components.applicationCardV2.applicationID")}
        details={claim.fineos_absence_id}
      />
      <TitleAndDetailSection
        title={t("components.applicationCardV2.employerEIN")}
        details={claim.employer_fein}
      />

      <GroupButtonSection
        buttonText={t(
          "components.applicationCardV2.viewStatusUpdatesAndDetails"
        )}
        href={routeWithParams("applications.uploadDocsOptions", {
          claim_id: claim.application_id,
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
        return null;
    }
  };

  return (
    <React.Fragment>
      <aside className="maxw-mobile-lg border-top-1 border-primary" />
      <article className="maxw-mobile-lg border-left border-right border-bottom border-base-lighter margin-bottom-3">
        <StatusCard />
      </article>
    </React.Fragment>
  );
};

ApplicationCardV2.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
  }).isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default ApplicationCardV2;
