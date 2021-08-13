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
import { isFeatureEnabled } from "../services/featureFlags";
import { useTranslation } from "../locales/i18n";

// REUSABLE STATUS CARD SECTIONS
/**
 * Single source for pre-styled status card
 * @property {ReactElement} children - Child components
 * @returns {ReactElement}
 */
const StatusCardContainer = ({ children }) => (
  <React.Fragment>
    <aside className="maxw-mobile-lg border-top-1 border-primary" />
    <article className="maxw-mobile-lg border-left border-right border-bottom border-base-lighter margin-bottom-3">
      {children}
    </article>
  </React.Fragment>
);

StatusCardContainer.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node,
  ]).isRequired,
};

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
 * @property {string} details - Details to provide (e.g., actual ID or EIN)
 * @property {string} title - Title of the detail being displayed (e.g., "Application ID")
 * @returns {ReactElement}
 */
const GroupDetailSection = ({ details, title }) => (
  <div className="padding-2 padding-bottom-1 padding-top-0 margin-top-0">
    <Heading level="4" size="6">
      {title}
    </Heading>
    <Heading className="margin-bottom-1 margin-top-1" level="4">
      {details}
    </Heading>
  </div>
);

GroupDetailSection.propTypes = {
  details: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
};

/**
 * Button section with top border and optional header text/section
 * @property {string} buttonText - Text to be displayed on button
 * @property {string} [headerText=''] - Optional header text
 * @property {string} href - Link/URL path for href attribute
 * @property {ReactElement} [iconComponent=null] - Optional icon component to pass
 * @returns {ReactElement}
 */
const GroupButtonSection = ({
  buttonText,
  headerText = "",
  href,
  iconComponent = null,
}) => {
  const GroupButtonHeader = () => {
    if (!headerText) return null;

    /**
     * @todo "in progress" status designs include a header
     * section which can be added here when needed.
     */
  };

  return (
    <div className="border-top border-base-lighter padding-2 margin-1 margin-bottom-0">
      <GroupButtonHeader />
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
  headerText: PropTypes.string,
  href: PropTypes.string.isRequired,
  iconComponent: PropTypes.elementType,
};

GroupButtonSection.defaultProps = {
  headerText: "",
  iconComponent: null,
};

/**
 * Section to view notices and upload documents
 * @property {Class} claim - Instance of BenefitsApplication
 * @property {Function} t - Translation function for localization
 * @returns {ReactElement}
 */
const ManageDocumentSection = ({ claim, t }) => {
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
  t: PropTypes.func.isRequired,
};

// STATUS CARDS
/**
 * Status card for claim.status = "Completed"
 * @property {Class} claim - Instance of BenefitsApplication
 * @property {Function} t - Translation function for localization
 * @returns {ReactElement}
 */
const CompletedStatusCard = ({ claim, t }) => {
  const iconComponent = (
    <Icon
      className="position-absolute flex-align-self-end margin-right-neg-105"
      fill="white"
      name="arrow_forward"
      size={3}
    />
  );

  const leaveReasonText = t("components.applicationCardV2.leaveReasonValue", {
    context: findKeyByValue(LeaveReason, claim.leave_details?.reason),
  });

  return (
    <StatusCardContainer>
      <HeaderSection title={leaveReasonText} />
      <GroupDetailSection
        title={t("components.applicationCardV2.applicationID")}
        details={claim.fineos_absence_id}
      />
      <GroupDetailSection
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
      <ManageDocumentSection claim={claim} t={t} />
    </StatusCardContainer>
  );
};

CompletedStatusCard.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  t: PropTypes.func.isRequired,
};

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 *
 * @property {object} appLogic - Data for application logic.<br>
 * @property {Array} [documents=[]] - Potential documents for user.<br>
 * @property {Class} claim - Instance of BenefitsApplication.<br>
 * @property {Function} t - Translation function for localization.<br>
 * @returns {ReactElement}
 */
export const ApplicationCardV2 = (props) => {
  const { claim } = props;
  const { t } = useTranslation();
  const statusProps = { ...props, t };

  // Determine status based on claim.status & feature flags
  const status =
    {
      [true]: null, // default
      [isFeatureEnabled("claimantShowStatusPage")]: "Completed",
    }.true || claim.status; // uses claim.status if no feature flags set

  switch (status) {
    case "Completed":
      return <CompletedStatusCard {...statusProps} />;

    default:
      return null;
  }
};

ApplicationCardV2.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.object.isRequired,
    documents: PropTypes.shape({
      download: PropTypes.func.isRequired,
    }),
  }).isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  documents: PropTypes.arrayOf(PropTypes.instanceOf(Document)),
};

ApplicationCardV2.defaultProps = {
  documents: [],
};

export default ApplicationCardV2;
