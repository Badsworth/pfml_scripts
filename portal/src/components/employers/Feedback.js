import React, { useEffect, useState } from "react";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConditionalContent from "../ConditionalContent";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { Trans } from "react-i18next";
import classnames from "classnames";
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
  const [shouldShowCommentBox, setShouldShowCommentBox] = useState(false);
  const errorMsg = appLogic.appErrors.fieldErrorMessage("comment");

  useEffect(() => {
    if (!shouldShowCommentBox) {
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

  const commentClasses = classnames("usa-form-group", {
    "usa-form-group--error": !!errorMsg,
  });
  const textAreaClasses = classnames("usa-textarea margin-top-3", {
    "usa-input--error": !!errorMsg,
  });

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
        <div className={commentClasses}>
          <FormLabel
            className="usa-label"
            htmlFor="comment"
            small
            errorMsg={errorMsg}
          >
            <Trans
              i18nKey="components.employersFeedback.commentSolicitation"
              tOptions={{
                context: buildContext() || "",
              }}
            />
          </FormLabel>
          <textarea
            className={textAreaClasses}
            name="comment"
            onChange={(event) => setComment(event.target.value)}
          />
        </div>
      </ConditionalContent>
    </React.Fragment>
  );
};

Feedback.propTypes = {
  appLogic: PropTypes.shape({
    appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
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
