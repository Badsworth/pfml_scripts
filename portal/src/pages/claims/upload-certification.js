import Claim, { LeaveReason } from "../../models/Claim";
import React, { useState } from "react";
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

const UploadCertification = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const [files, setFiles] = useState([]);
  const reasonKey = findKeyByValue(LeaveReason, claim.leave_details.reason);

  // TODO (CP-396): connect this page to the API file upload endpoint.
  const handleSave = () => {
    appLogic.goToNextPage(null, props.query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsUploadCertification.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsUploadCertification.sectionLabel", {
          context: reasonKey,
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
          tOptions={{ context: reasonKey }}
        />
      </Lead>
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
