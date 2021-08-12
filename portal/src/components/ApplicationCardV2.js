import BenefitsApplication from "../models/BenefitsApplication";
import Document from "../models/Document";
import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import Icon from "../components/Icon";
import LeaveReason from "../models/LeaveReason";
import PropTypes from "prop-types";
import React from "react";
import findKeyByValue from "../utils/findKeyByValue";
import routeWithParams, {
  createRouteWithQuery,
} from "../utils/routeWithParams";

import { useTranslation } from "../locales/i18n";

/**
 * TODO action items:
 * @todo configure translation strings as needed
 * @todo add prop types for each of the components
 * @todo include feature flag(s) in the logic
 */

/**
 * Storing strings here until localization is hooked up.
 */
const text = {
  applicationID: "Application ID",
  employerEIN: "Employer Identification Number",
  manageApplicationDocuments: "Manage your application documents",
  uploadDocuments: "Upload documents",
  viewNotices: "View notices",
  viewStatusUpdatesAndDetails: "View status updates and details",
};

// REUSABLE STATUS CARD SECTIONS
/**
 * Single source for pre-styled status card
 * @param {ReactElement} children - Child components
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

/**
 * Group together details for status cards
 * @param {string} title - Title of the detail being displayed (e.g., "Application ID")
 * @param {string} details - Details to provide (e.g., actual ID or EIN)
 * @returns {ReactElement}
 */
const GroupDetailSection = ({ title, details }) => (
  <div className="padding-2 padding-bottom-1 padding-top-0 margin-top-0">
    <Heading level="4" size="6">
      {title}
    </Heading>
    <Heading className="margin-bottom-1 margin-top-1" level="4">
      {details}
    </Heading>
  </div>
);

/**
 * Button section with top border and optional header text/section
 * @param {string} buttonText - Text to be displayed on button
 * @param {ReactElement} [icon=null] - Optional children to pass (e.g., icon)
 * @param {string} href - Link/URL path for href attribute
 * @param {string} [headerText=''] - Optional header text
 * @returns {ReactElement}
 */
const GroupButtonSection = ({
  iconComponent = null,
  href,
  buttonText,
  headerText = "",
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

/**
 * Section to view notices and upload documents
 * @param {Class} claim - Instance of BenefitsApplication
 * @returns {ReactElement}
 */
const ManageDocumentSection = ({ claim }) => {
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
        {text.manageApplicationDocuments}
      </Heading>
      <ButtonLink
        className="display-block margin-bottom-3"
        href={viewNoticesLink}
        variation="unstyled"
      >
        {text.viewNotices}
      </ButtonLink>

      <ButtonLink
        className="display-block margin-bottom-2"
        href={uploadDocumentsLink}
        variation="unstyled"
      >
        {text.uploadDocuments}
      </ButtonLink>
    </div>
  );
};

// STATUS CARDS
/**
 * Status card for claim.status = "Completed"
 * @param {Class} claim - Instance of BenefitsApplication
 * @param {function} t - Translation function for localization
 * @returns {ReactElement}
 */
const CompletedStatusCard = ({ claim, t }) => {
  // TODO: configure as text object?
  const leaveReasonText = t("components.applicationCard.leaveReasonValue", {
    context: findKeyByValue(LeaveReason, claim.leave_details?.reason),
  });

  const iconComponent = (
    <Icon
      className="position-absolute flex-align-self-end margin-right-neg-105"
      fill="white"
      name="arrow_forward"
      size="3"
    />
  );

  return (
    <StatusCardContainer>
      <HeaderSection title={leaveReasonText} />
      <GroupDetailSection
        title={text.applicationID}
        details={claim.fineos_absence_id}
      />
      <GroupDetailSection
        title={text.employerEIN}
        details={claim.employer_fein}
      />
      <GroupButtonSection
        buttonText={text.viewStatusUpdatesAndDetails}
        href={routeWithParams("applications.uploadDocsOptions", {
          claim_id: claim.application_id,
        })}
        iconComponent={iconComponent}
      />
      <ManageDocumentSection claim={claim} />
    </StatusCardContainer>
  );
};

/**
 * Main entry point for an existing benefits Application, allowing
 * claimants to continue an in progress application, view what
 * they've submitted, view notices and instructions, or upload
 * additional docs.
 *
 * @param {object} appLogic - Data for application logic.<br>
 * @param {array} [documents=[]] - Potential documents for user.<br>
 * @param {Class} claim - Instance of BenefitsApplication.<br>
 * @param {function} t - Translation function for localization.<br>
 * @returns {ReactElement}
 */
export const ApplicationCardV2 = (props) => {
  const {
    claim: { status },
  } = props;
  const { t } = useTranslation();
  const statusProps = { ...props, t };

  // TODO: connect feature flag(s) here
  // TODO: handle other statuses here
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
