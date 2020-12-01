import React, { useEffect, useState } from "react";
import ConditionalContent from "../ConditionalContent";
import FileCardList from "../FileCardList";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
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
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [shouldShowCommentBox, setShouldShowCommentBox] = useState(false);

  useEffect(() => {
    if (!shouldShowCommentBox) {
      setUploadedFiles([]);
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

  return (
    <React.Fragment>
      <InputChoiceGroup
        choices={[
          {
            checked: !shouldShowCommentBox,
            disabled: isDenyingRequest || isEmployeeNoticeInsufficient,
            label: t("pages.employersClaimsReview.feedback.choiceNo"),
            value: "false",
          },
          {
            checked: shouldShowCommentBox,
            label: t("pages.employersClaimsReview.feedback.choiceYes"),
            value: "true",
          },
        ]}
        label={
          <ReviewHeading level="2">
            {t("pages.employersClaimsReview.feedback.instructionsLabel")}
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
            {t("pages.employersClaimsReview.feedback.tellUsMoreLabel")}
          </FormLabel>
          {isReportingFraud && (
            <p level="4" className="text-error">
              {t(
                "pages.employersClaimsReview.feedback.commentSolicitation_fraud"
              )}
            </p>
          )}
          {isEmployeeNoticeInsufficient && (
            <p level="4" className="text-error">
              {t(
                "pages.employersClaimsReview.feedback.commentSolicitation_employeeNotice"
              )}
            </p>
          )}
          {!isReportingFraud && isDenyingRequest && (
            <p level="4" className="text-error">
              {t(
                "pages.employersClaimsReview.feedback.commentSolicitation_employerDecision"
              )}
            </p>
          )}
          <textarea
            className="usa-textarea margin-top-3"
            name="comment"
            onChange={(event) => setComment(event.target.value)}
          />
          <FormLabel small>
            {t(
              "pages.employersClaimsReview.feedback.supportingDocumentationLabel"
            )}
          </FormLabel>
          <FileCardList
            filesWithUniqueId={uploadedFiles}
            setFiles={setUploadedFiles}
            setAppErrors={appLogic.setAppErrors}
            fileHeadingPrefix={t(
              "pages.employersClaimsReview.feedback.fileHeadingPrefix"
            )}
            addFirstFileButtonText={t(
              "pages.employersClaimsReview.feedback.addFirstFileButton"
            )}
            addAnotherFileButtonText={t(
              "pages.employersClaimsReview.feedback.addAnotherFileButton"
            )}
          />
        </React.Fragment>
      </ConditionalContent>
    </React.Fragment>
  );
};

Feedback.propTypes = {
  appLogic: PropTypes.shape({
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  isReportingFraud: PropTypes.bool,
  isDenyingRequest: PropTypes.bool,
  isEmployeeNoticeInsufficient: PropTypes.bool,
  comment: PropTypes.string.isRequired,
  setComment: PropTypes.func.isRequired,
};

export default Feedback;
