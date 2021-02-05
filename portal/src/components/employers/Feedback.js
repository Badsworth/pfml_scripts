import React, { useEffect, useState } from "react";
import ConditionalContent from "../ConditionalContent";
import FileCardList from "../FileCardList";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import TempFileCollection from "../../models/TempFileCollection";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import useTempFileCollection from "../../hooks/useTempFileCollection";
import { useTranslation } from "../../locales/i18n";

/**
 * Display language and form for Leave Admin to include comment
 * in the Leave Admin claim review page.
 */

const Feedback = ({
  appLogic,
  isReportingFraud,
  isDenyingRequest,
  isEmployeeNoticeInsufficient,
  comment,
  setComment,
}) => {
  // TODO (EMPLOYER-583) add frontend validation
  const { t } = useTranslation();
  const {
    tempFiles,
    addTempFiles,
    removeTempFile,
    setTempFiles,
  } = useTempFileCollection(new TempFileCollection(), {
    clearErrors: appLogic.clearErrors,
  });
  const [shouldShowCommentBox, setShouldShowCommentBox] = useState(false);

  useEffect(() => {
    if (!shouldShowCommentBox) {
      setTempFiles(new TempFileCollection());
      setComment("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldShowCommentBox]);

  useEffect(() => {
    setShouldShowCommentBox(
      isDenyingRequest || isEmployeeNoticeInsufficient || !!comment
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDenyingRequest, isEmployeeNoticeInsufficient]);

  const buildContext = () => {
    if (isReportingFraud) return "fraud";
    if (!isReportingFraud && isDenyingRequest) return "employerDecision";
    if (!isDenyingRequest && isEmployeeNoticeInsufficient)
      return "employeeNotice";
  };

  const shouldShowFileUpload = isFeatureEnabled("employerShowFileUpload");

  return (
    <React.Fragment>
      <InputChoiceGroup
        smallLabel
        choices={[
          {
            checked: shouldShowCommentBox,
            label: t("components.employersFeedback.choiceYes"),
            value: "true",
          },
          {
            checked: !shouldShowCommentBox,
            disabled: isDenyingRequest || isEmployeeNoticeInsufficient,
            label: t("components.employersFeedback.choiceNo"),
            value: "false",
          },
        ]}
        label={
          <ReviewHeading level="2">
            {t("components.employersFeedback.instructionsLabel")}
          </ReviewHeading>
        }
        name="shouldShowCommentBox"
        onChange={(event) => {
          const hasSelectedYes = event.target.value === "true";
          setShouldShowCommentBox(hasSelectedYes);
          if (!hasSelectedYes) setComment("");
        }}
        type="radio"
      />
      <ConditionalContent
        getField={() => comment}
        clearField={() => setComment("")}
        updateFields={(event) => setComment(event.target.value)}
        visible={shouldShowCommentBox}
      >
        <React.Fragment>
          <FormLabel className="usa-label" htmlFor="comment" small>
            <Trans
              i18nKey="components.employersFeedback.commentSolicitation"
              tOptions={{
                context: buildContext() || "",
              }}
            />
          </FormLabel>
          <textarea
            className="usa-textarea margin-top-3"
            name="comment"
            onChange={(event) => setComment(event.target.value)}
          />
          {/* TODO (EMPLOYER-665): Show file upload */}
          {shouldShowFileUpload && (
            <React.Fragment>
              <FormLabel small>
                {t("components.employersFeedback.supportingDocumentationLabel")}
              </FormLabel>
              <FileCardList
                tempFiles={tempFiles}
                onAddTempFiles={addTempFiles}
                onRemoveTempFile={removeTempFile}
                onInvalidFilesError={appLogic.catchError}
                fileHeadingPrefix={t(
                  "components.employersFeedback.fileHeadingPrefix"
                )}
                addFirstFileButtonText={t(
                  "components.employersFeedback.addFirstFileButton"
                )}
                addAnotherFileButtonText={t(
                  "components.employersFeedback.addAnotherFileButton"
                )}
              />
            </React.Fragment>
          )}
        </React.Fragment>
      </ConditionalContent>
    </React.Fragment>
  );
};

Feedback.propTypes = {
  appLogic: PropTypes.shape({
    clearErrors: PropTypes.func.isRequired,
    catchError: PropTypes.func.isRequired,
  }).isRequired,
  isReportingFraud: PropTypes.bool,
  isDenyingRequest: PropTypes.bool,
  isEmployeeNoticeInsufficient: PropTypes.bool,
  comment: PropTypes.string.isRequired,
  setComment: PropTypes.func.isRequired,
};

export default Feedback;
