import React, { useState } from "react";
import FileCardList from "../../components/FileCardList";
import FileUploadDetails from "../../components/FileUploadDetails";
import FormLabel from "../../components/FormLabel";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import routeWithParams from "../../utils/routeWithParams";
import { useTranslation } from "../../locales/i18n";

const UploadOtherId = (props) => {
  const { t } = useTranslation();
  const [otherIdFiles, setOtherIdFiles] = useState([]);
  const lead = t("pages.claimsUploadOtherId.lead");
  const documentList = t("pages.claimsUploadOtherId.documentList", {
    returnObjects: true,
  });

  // @todo: CP-396 connect this page to the API file upload endpoint.
  const handleSave = () => {};

  return (
    <QuestionPage
      title={t("pages.claimsUploadOtherId.title")}
      onSave={handleSave}
      nextPage={routeWithParams("claims.ssn", props.query)}
    >
      <FormLabel>{t("pages.claimsUploadOtherId.sectionLabel")}</FormLabel>
      {/* should we only use margin-bottom? */}
      <div className="margin-top-2 usa-intro">
        {lead}
        <ul>
          {documentList.map((listItem, index) => (
            <li key={index}>{listItem}</li>
          ))}
        </ul>
      </div>
      <FileUploadDetails />
      <FileCardList
        files={otherIdFiles}
        setFiles={setOtherIdFiles}
        fileHeadingPrefix={t("pages.claimsUploadOtherId.fileHeadingPrefix")}
        addFirstFileButtonText={t(
          "pages.claimsUploadOtherId.addFirstFileButtonText"
        )}
        addAnotherFileButtonText={t(
          "pages.claimsUploadOtherId.addAnotherFileButtonText"
        )}
      />
    </QuestionPage>
  );
};

UploadOtherId.propTypes = {
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default UploadOtherId;
