import Claim, { LeaveReason, ReasonQualifier } from "../../models/Claim";
import React, { useState } from "react";
import ConditionalContent from "../../components/ConditionalContent";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

export const UploadCertification = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const [files, setFiles] = useState([]);
  const claimReason = claim.leave_details.reason;
  const claimReasonQualifier = claim.leave_details.reason_qualifier;

  const conditionalContext = {
    [LeaveReason.bonding]: {
      [ReasonQualifier.newBorn]: "bonding_newborn",
      [ReasonQualifier.adoption]: "bonding_adopt_foster",
      [ReasonQualifier.fosterCare]: "bonding_adopt_foster",
    },
    [LeaveReason.medical]: "medical",
  };
  let leadTextContext;
  switch (claimReason) {
    case LeaveReason.medical:
      leadTextContext = conditionalContext[claimReason];
      break;
    case LeaveReason.bonding:
      leadTextContext = conditionalContext[claimReason][claimReasonQualifier];
      break;
  }

  const handleSave = async () => {
    await appLogic.documents.attach(
      claim.application_id,
      files,
      "State Managed Paid Leave Confirmation" // TODO (CP-962): replace this with an enum value, and set based on leaveReason
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsUploadCertification.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsUploadCertification.sectionLabel", {
          context: findKeyByValue(LeaveReason, claimReason),
        })}
      </Heading>
      <Lead>
        <Trans
          i18nKey="pages.claimsUploadCertification.lead"
          components={{
            "healthcare-provider-form-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.healthcareProviderForm}
              />
            ),
          }}
          tOptions={{
            context: leadTextContext,
          }}
        />
      </Lead>
      <ConditionalContent
        visible={
          claim.isBondingLeave &&
          claimReasonQualifier === ReasonQualifier.newBorn
        }
      >
        <ul className="usa-list">
          {t("pages.claimsUploadCertification.leadListNewborn", {
            returnObjects: true,
          }).map((listItem, index) => (
            <li key={index}>{listItem}</li>
          ))}
        </ul>
      </ConditionalContent>
      <FileUploadDetails />
      <FileCardList
        files={files}
        setFiles={setFiles}
        setAppErrors={appLogic.setAppErrors}
        fileHeadingPrefix={t(
          "pages.claimsUploadCertification.fileHeadingPrefix"
        )}
        addFirstFileButtonText={t(
          "pages.claimsUploadCertification.addFirstFileButton"
        )}
        addAnotherFileButtonText={t(
          "pages.claimsUploadCertification.addAnotherFileButton"
        )}
      />
    </QuestionPage>
  );
};

UploadCertification.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(UploadCertification);
