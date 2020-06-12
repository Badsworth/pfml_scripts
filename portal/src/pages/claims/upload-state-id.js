import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import FormLabel from "../../components/FormLabel";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import routeWithParams from "../../utils/routeWithParams";
import { useTranslation } from "../../locales/i18n";

const UploadStateId = (props) => {
  const { t } = useTranslation();
  const [stateIdFiles, setStateIdFiles] = useState([]);

  // @todo: CP-396 connect this page to the API file upload endpoint.
  const handleSave = () => {};

  return (
    <QuestionPage
      title={t("pages.claimsUploadStateId.title")}
      onSave={handleSave}
      nextPage={routeWithParams("claims.ssn", props.query)}
    >
      <FormLabel>{t("pages.claimsUploadStateId.sectionLabel")}</FormLabel>
      <Lead>{t("pages.claimsUploadStateId.lead")}</Lead>
      <FileUploadDetails />
      <FileCardList
        files={stateIdFiles}
        setFiles={setStateIdFiles}
        fileHeadingPrefix={t("pages.claimsUploadStateId.fileHeadingPrefix")}
        addFirstFileButtonText={t(
          "pages.claimsUploadStateId.addFirstFileButtonText"
        )}
        addAnotherFileButtonText={t(
          "pages.claimsUploadStateId.addAnotherFileButtonText"
        )}
      />
    </QuestionPage>
  );
};

UploadStateId.propTypes = {
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default UploadStateId;
