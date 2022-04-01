import React, { useEffect } from "react";
import {
  getLeaveCertificationDocs,
  getLegalNotices,
} from "../../../models/Document";
import withEmployerClaim, {
  WithEmployerClaimProps,
} from "../../../hoc/withEmployerClaim";
import BackButton from "../../../components/BackButton";
import CertificationsAndAbsencePeriods from "../../../features/employer-review/CertificationsAndAbsencePeriods";
import DownloadableDocument from "../../../components/DownloadableDocument";
import EmployeeInformation from "../../../features/employer-review/EmployeeInformation";
import Heading from "../../../components/core/Heading";
import HeadingPrefix from "src/components/core/HeadingPrefix";
import Lead from "../../../components/core/Lead";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Status = (props: WithEmployerClaimProps) => {
  const { appLogic, claim } = props;
  const {
    employers: { claimDocumentsMap, downloadDocument },
  } = appLogic;
  const { t } = useTranslation();

  const absenceId = claim.fineos_absence_id;

  useEffect(() => {
    appLogic.employers.loadDocuments(claim.fineos_absence_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absenceId]);

  const allDocuments = claimDocumentsMap.get(absenceId)?.items || [];
  const legalNotices = getLegalNotices(allDocuments);
  const certificationDocuments = getLeaveCertificationDocs(allDocuments);

  /**
   * We use this page as the entry point for leave admins viewing an individual claim.
   * We need to determine whether they should see the status page or the review page.
   */
  if (claim.is_reviewable) {
    appLogic.portalFlow.goToPageFor(
      "REDIRECT_REVIEWABLE_CLAIM",
      {},
      { absence_id: absenceId },
      { redirect: true }
    );

    return null;
  }

  return (
    <React.Fragment>
      <BackButton />
      <HeadingPrefix>
        {t("pages.employersClaimsReview.absenceIdLabel", {
          absenceId: claim.fineos_absence_id,
        })}
      </HeadingPrefix>
      <Title>
        {t("pages.employersClaimsStatus.title", { name: claim.fullName })}
      </Title>
      <Lead>
        <Trans
          i18nKey="pages.employersClaimsStatus.lead"
          components={{
            "dfml-regulations-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.dfmlRegulations}
              />
            ),
          }}
        />
      </Lead>
      <React.Fragment>
        <EmployeeInformation claim={claim} />
        <CertificationsAndAbsencePeriods
          claim={claim}
          documents={certificationDocuments}
          downloadDocument={downloadDocument}
        />
      </React.Fragment>

      {legalNotices.length > 0 && (
        <div className="padding-top-2">
          <Heading level="2">
            {t("pages.employersClaimsStatus.noticesLabel")}
          </Heading>
          <ul
            className="usa-list usa-list--unstyled margin-top-2"
            data-testid="documents"
          >
            {legalNotices.map((document) => (
              <li key={document.fineos_document_id} className="margin-bottom-2">
                <DownloadableDocument
                  absenceId={absenceId}
                  downloadClaimDocument={downloadDocument}
                  document={document}
                  showCreatedAt
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </React.Fragment>
  );
};

export default withEmployerClaim(Status);
