import React, { useEffect } from "react";
import { find, get, groupBy, has, isEmpty, map } from "lodash";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import ClaimDetail from "../../models/ClaimDetail";
import DocumentCollection from "../../models/DocumentCollection";
import { DocumentType } from "../../models/Document";
import Heading from "../../components/Heading";
import LeaveReason from "../../models/LeaveReason";
import LegalNoticeList from "../../components/LegalNoticeList.js";
import PropTypes from "prop-types";
import Spinner from "../../components/Spinner";
import Tag from "../../components/Tag";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import findDocumentsByTypes from "../../utils/findDocumentsByTypes";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDate from "../../utils/formatDate";
import { isFeatureEnabled } from "../../services/featureFlags";
import routeWithParams from "../../utils/routeWithParams";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

const nextStepsRoute = {
  newborn: "applications.upload.bondingProofOfBirth",
  adoption: "applications.upload.bondingProofOfPlacement",
};

export const Status = ({ appLogic, query }) => {
  const { t } = useTranslation();
  const {
    claims: { claimDetail, isLoadingClaimDetail, loadClaimDetail },
    documents: {
      documents,
      download: downloadDocument,
      hasLoadedClaimDocuments,
      loadAll: loadClaimDocuments,
    },
    portalFlow,
  } = appLogic;
  const { absence_case_id } = query;

  useEffect(() => {
    if (!isFeatureEnabled("claimantShowStatusPage")) {
      portalFlow.goTo(routes.applications.index);
    }
  }, [portalFlow]);

  useEffect(() => {
    loadClaimDetail(absence_case_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absence_case_id]);

  useEffect(() => {
    const application_id = get(claimDetail, "application_id");
    if (application_id) {
      loadClaimDocuments(application_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimDetail]);

  const appErrorsByType = groupBy(appLogic.appErrors.items, "name");

  if (has(appErrorsByType, "ClaimDetailLoadError")) return null;

  // Check both because claimDetail could be cached from a different status page.
  if (isLoadingClaimDetail || !claimDetail)
    return (
      <div className="margin-top-8 text-center">
        <Spinner
          aria-valuetext={t("pages.claimsStatus.loadingClaimDetailLabel")}
        />
      </div>
    );

  const absenceDetails = claimDetail.absencePeriodsByReason;
  const legalNotices = documents.legalNotices;

  const ViewYourNotices = () => {
    const className = "border-top border-base-lighter padding-y-2";
    const hasDocumentsLoadError = has(appErrorsByType, "DocumentsLoadError");
    const shouldShowSpinner =
      !hasLoadedClaimDocuments(claimDetail.application_id) &&
      !hasDocumentsLoadError;
    const nothingToShow = legalNotices.length === 0 || hasDocumentsLoadError;

    if (shouldShowSpinner) {
      // claim documents are loading.
      return (
        <div className={className}>
          <Spinner
            aria-valuetext={t("pages.claimsStatus.loadingLegalNoticesLabel")}
          />
        </div>
      );
    }

    if (nothingToShow) {
      return null;
    }

    return (
      <div className={className}>
        <Heading className="margin-bottom-1" level="2" id="view_notices">
          {t("pages.claimsStatus.viewNoticesHeading")}
        </Heading>
        <LegalNoticeList
          documents={legalNotices}
          onDownloadClick={downloadDocument}
        />
      </div>
    );
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
  const [firstAbsenceDetail] = Object.keys(absenceDetails);
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
          {t("pages.claimsStatus.leaveReasonValueHeader", {
            context: findKeyByValue(LeaveReason, firstAbsenceDetail),
          })}
        </Heading>
        <div className="display-flex border-base-lighter margin-bottom-3 bg-base-lightest padding-2">
          <div className="padding-right-10">
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.applicationID")}
            </Heading>
            <p className="text-bold">{absence_case_id}</p>
          </div>
          <div>
            <Heading weight="normal" level="2" size="4">
              {t("pages.claimsStatus.employerEIN")}
            </Heading>
            <p className="text-bold">{claimDetail.employer.employer_fein}</p>
          </div>
        </div>
        <ApplicationUpdates
          absenceDetails={absenceDetails}
          applicationId={claimDetail.application_id}
          docList={documents.items}
        />
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
          <ButtonLink
            className="measure-6 margin-bottom-3"
            href={routeWithParams("applications.upload.index", {
              absence_case_id: claimDetail.application_id,
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
    claims: PropTypes.shape({
      claimDetail: PropTypes.instanceOf(ClaimDetail),
      isLoadingClaimDetail: PropTypes.bool,
      loadClaimDetail: PropTypes.func.isRequired,
    }).isRequired,
    documents: PropTypes.shape({
      documents: PropTypes.instanceOf(DocumentCollection).isRequired,
      download: PropTypes.func.isRequired,
      hasLoadedClaimDocuments: PropTypes.func.isRequired,
      loadAll: PropTypes.func.isRequired,
    }),
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  query: PropTypes.shape({
    absence_case_id: PropTypes.string,
  }).isRequired,
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
    <div key={absenceItemName} className="border-base-lighter margin-bottom-2">
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
                    context: period_type.split(" ")[0].toLowerCase(),
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

LeaveDetails.propTypes = {
  absenceDetails: PropTypes.object,
};

export const ApplicationUpdates = ({
  absenceDetails = {},
  application_id,
  docList = [],
}) => {
  const { t } = useTranslation();

  const shouldRenderProofOfBirthButton = (
    absenceItemName,
    absenceType,
    docList
  ) =>
    absenceItemName === LeaveReason[absenceType] &&
    !findDocumentsByTypes(docList, [
      DocumentType.certification[absenceItemName],
    ]).length;

  const renderOptions = (absenceItemName, absenceItem, docList) => {
    const isNewBornQualifier = find(
      absenceItem,
      (item) => item && item.reason_qualifier_one === "Newborn"
    );
    if (
      (shouldRenderProofOfBirthButton(absenceItemName, "bonding", docList) &&
        isNewBornQualifier) ||
      shouldRenderProofOfBirthButton(absenceItemName, "pregnancy", docList)
    ) {
      return "newborn";
    } else if (
      shouldRenderProofOfBirthButton(absenceItemName, "bonding", docList) &&
      !isNewBornQualifier
    ) {
      return "adoption";
    }
  };

  return isEmpty(absenceDetails) ? null : (
    <div className="border-bottom border-base-lighter padding-bottom-2 margin-bottom-2">
      <Heading level="2">
        {t("pages.claimsStatus.applicationUpdatesHeading")}
      </Heading>
      <Heading level="3">{t("pages.claimsStatus.whatHappensNext")}</Heading>
      {
        map(absenceDetails, (absenceItem, absenceItemName) => {
          const typeOfProof = renderOptions(
            absenceItemName,
            absenceItem,
            docList
          );
          return nextStepsRoute[typeOfProof] ? (
            <div key={absenceItemName}>
              <p>
                {t("pages.claimsStatus.whatYouNeedToDoText", {
                  context: typeOfProof,
                })}
              </p>
              <ButtonLink
                className="measure-12"
                href={routeWithParams(nextStepsRoute[typeOfProof], {
                  absence_case_id: application_id,
                  additionalDoc: true,
                })}
              >
                {t("pages.claimsStatus.whatHappensNextButton", {
                  context: typeOfProof,
                })}
              </ButtonLink>
            </div>
          ) : null;
        })[0]
      }
    </div>
  );
};

ApplicationUpdates.propTypes = {
  absenceDetails: PropTypes.object,
  application_id: PropTypes.string,
  docList: PropTypes.array,
};
