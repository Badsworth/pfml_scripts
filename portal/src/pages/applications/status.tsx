import Document, { DocumentType } from "../../models/Document";
import React, { useEffect, useState } from "react";
import BackButton from "../../components/BackButton";
import Heading from "../../components/Heading";
import LegalNoticeList from "../../components/LegalNoticeList.js";
import PropTypes from "prop-types";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { handleError } from "../../api/BaseApi";
import { isFeatureEnabled } from "../../services/featureFlags";
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

export const Status = ({ appLogic, docList = TEST_DOC }) => {
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
        <Heading className="margin-bottom-1" level="2">
          {t("pages.claimsStatus.viewNoticesHeading")}
        </Heading>
        <LegalNoticeList
          documents={documents}
          // @ts-expect-error ts-migrate(2322) FIXME: Type '{ documents: Document[]; handleDownload: any... Remove this comment to see the full error message
          handleDownload={appLogic.documents.download}
        />
      </div>
    ) : null;
  };

  const containerClassName = "border-top border-base-lighter padding-top-2";

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsStatus.backButtonLabel")}
        href={routes.applications.index}
      />
      <div className="measure-6">
        <Title weight="normal" small={true}>
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
        <ViewYourNotices />
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
};

export default Status;
