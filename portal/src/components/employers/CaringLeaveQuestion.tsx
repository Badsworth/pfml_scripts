import Alert from "../core/Alert";
import ConditionalContent from "../ConditionalContent";
import FormLabel from "../core/FormLabel";
import InputChoiceGroup from "../core/InputChoiceGroup";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import { Trans } from "react-i18next";
import classnames from "classnames";
import isBlank from "src/utils/isBlank";
import routes from "src/routes";
import { useTranslation } from "src/locales/i18n";

interface CaringLeaveQuestionProps {
  errorMsg: React.ReactNode;
  believeRelationshipAccurate?: "Yes" | "Unknown" | "No";
  onChangeBelieveRelationshipAccurate?: (arg: string) => void;
  onChangeRelationshipInaccurateReason: (arg: string) => void;
}

const CaringLeaveQuestion = (props: CaringLeaveQuestionProps) => {
  const { t } = useTranslation();
  const {
    errorMsg,
    believeRelationshipAccurate,
    onChangeBelieveRelationshipAccurate,
    onChangeRelationshipInaccurateReason,
  } = props;

  const inaccurateReasonClasses = classnames("usa-form-group", {
    "usa-form-group--error": !isBlank(errorMsg),
  });

  const textAreaClasses = classnames("usa-textarea margin-top-3", {
    "usa-input--error": !isBlank(errorMsg),
  });

  return (
    <React.Fragment>
      <InputChoiceGroup
        smallLabel
        name="believeRelationshipAccurate"
        onChange={(e) => {
          if (onChangeBelieveRelationshipAccurate)
            onChangeBelieveRelationshipAccurate(e.target.value);
        }}
        choices={[
          {
            checked: believeRelationshipAccurate === "Yes",
            label: t("components.employersLeaveDetails.choiceYes"),
            value: "Yes",
          },
          {
            checked: believeRelationshipAccurate === "Unknown",
            label: t("components.employersLeaveDetails.choiceUnknown"),
            value: "Unknown",
          },
          {
            checked: believeRelationshipAccurate === "No",
            label: t("components.employersLeaveDetails.choiceNo"),
            value: "No",
          },
        ]}
        label={
          <ReviewHeading level="2">
            {t(
              "components.employersLeaveDetails.familyMemberRelationshipLabel"
            )}
          </ReviewHeading>
        }
        hint={
          <Trans
            i18nKey="components.employersLeaveDetails.familyMemberRelationshipHint"
            components={{
              "eligible-relationship-link": (
                <a
                  target="_blank"
                  rel="noopener"
                  href={routes.external.massgov.caregiverRelationship}
                />
              ),
            }}
          />
        }
        type="radio"
      />

      <ConditionalContent visible={believeRelationshipAccurate === "No"}>
        <Alert
          state="warning"
          heading={t(
            "components.employersLeaveDetails.inaccurateRelationshipAlertHeading"
          )}
          headingSize="3"
          className="measure-5 margin-y-3"
        >
          {t(
            "components.employersLeaveDetails.inaccurateRelationshipAlertLead"
          )}
        </Alert>
        <div
          className={inaccurateReasonClasses}
          data-testid="inaccurate_reason"
        >
          <FormLabel
            inputId="relationshipInaccurateReason"
            small
            errorMsg={errorMsg}
          >
            {t("components.employersLeaveDetails.commentHeading")}
          </FormLabel>
          <textarea
            className={textAreaClasses}
            name="relationshipInaccurateReason"
            onChange={(event) =>
              onChangeRelationshipInaccurateReason(event.target.value)
            }
            id="relationshipInaccurateReason"
          />
        </div>
      </ConditionalContent>

      <ConditionalContent visible={believeRelationshipAccurate === "Unknown"}>
        <Alert state="info" className="measure-5 margin-y-3">
          {t("components.employersLeaveDetails.unknownRelationshipAlertLead")}
        </Alert>
      </ConditionalContent>
    </React.Fragment>
  );
};

export default CaringLeaveQuestion;
