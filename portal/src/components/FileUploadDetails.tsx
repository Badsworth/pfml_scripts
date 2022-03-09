import Details from "./core/Details";
import Heading from "./core/Heading";
import React from "react";
import { Trans } from "react-i18next";
import { useTranslation } from "../locales/i18n";

/**
 * A pre-populated Details component with information about uploading files. This component is
 * intended to be used on pages which use one or more FileCardList components.
 */
function FileUploadDetails() {
  const { t } = useTranslation();

  return (
    <Details label={t("components.fileUploadDetails.label")}>
      <Heading level="2" size="4">
        {t("components.fileUploadDetails.fileTypesHeading")}
      </Heading>
      <Trans
        i18nKey="components.fileUploadDetails.fileTypesList"
        components={{
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />

      <Heading level="2" size="4">
        {t("components.fileUploadDetails.conversionHeading")}
      </Heading>
      <Trans
        i18nKey="components.fileUploadDetails.conversionList"
        components={{
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />

      <Heading level="2" size="4">
        {t("components.fileUploadDetails.attachmentHeading")}
      </Heading>
      <Trans
        i18nKey="components.fileUploadDetails.attachmentList"
        components={{
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
    </Details>
  );
}

export default FileUploadDetails;
