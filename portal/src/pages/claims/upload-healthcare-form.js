import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

const UploadHealthcareForm = (props) => {
  const { t } = useTranslation();
  const [files, setFiles] = useState([]);

  // @todo: CP-396 connect this page to the API file upload endpoint.
  const handleSave = () => {
    props.appLogic.goToNextPage(null, props.query);
  };

  return (
    <QuestionPage
      title={t("pages.claimsUploadHealthcareForm.title")}
      onSave={handleSave}
    >
      <Heading level="2" size="1">
        {t("pages.claimsUploadHealthcareForm.sectionLabel")}
      </Heading>
      <Lead>
        <Trans
          i18nKey="pages.claimsUploadHealthcareForm.lead"
          components={{
            "healthcare-provider-form-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.healthcareProviderForm}
              />
            ),
          }}
        />
      </Lead>
      <FileUploadDetails />
      <FileCardList
        files={files}
        setFiles={setFiles}
        setAppErrors={props.appLogic.setAppErrors}
        fileHeadingPrefix={t(
          "pages.claimsUploadHealthcareForm.fileHeadingPrefix"
        )}
        addFirstFileButtonText={t(
          "pages.claimsUploadHealthcareForm.addFirstFileButton"
        )}
        addAnotherFileButtonText={t(
          "pages.claimsUploadHealthcareForm.addAnotherFileButton"
        )}
      />
    </QuestionPage>
  );
};

UploadHealthcareForm.propTypes = {
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(UploadHealthcareForm);
