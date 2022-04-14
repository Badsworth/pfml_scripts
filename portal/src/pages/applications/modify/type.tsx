import ChangeRequest, {
  ChangeRequestType,
} from "../../../models/ChangeRequest";
import withUser, { WithUserProps } from "../../../hoc/withUser";
import ClaimDetail from "src/models/ClaimDetail";
import ConditionalContent from "src/components/ConditionalContent";
import Fieldset from "src/components/core/Fieldset";
import FormLabel from "../../../components/core/FormLabel";
import InputChoiceGroup from "src/components/core/InputChoiceGroup";
import InputDate from "src/components/core/InputDate";
import PageNotFound from "../../../components/PageNotFound";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
import ReviewRow from "src/components/ReviewRow";
import { Trans } from "react-i18next";
import formatDate from "src/utils/formatDate";
import { isFeatureEnabled } from "../../../services/featureFlags";
import { pick } from "lodash";
import routes from "src/routes";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "src/hooks/useFunctionalInputProps";
import { useTranslation } from "../../../locales/i18n";

export const fields = [
  "change_request.change_request_type",
  "change_request.end_date",
];

type TypeProps = WithUserProps & {
  query: {
    change_request_id: string;
  };
  change_request?: ChangeRequest;
  claim_detail?: ClaimDetail;
};

export const Type = (props: TypeProps) => {
  // TODO (PORTAL-2030): Remove once attached to HOC
  const claim_detail =
    props.claim_detail ||
    new ClaimDetail({
      absence_periods: [
        {
          absence_period_start_date: "2022-01-01",
          absence_period_end_date: "2022-01-01",
          fineos_leave_request_id: "id-1",
          period_type: "Continuous",
          reason: "Care for a Family Member",
          request_decision: "Approved",
          reason_qualifier_one: "",
          reason_qualifier_two: "",
        },
      ],
    });
  const change_request = props.change_request || new ChangeRequest({});

  const { t } = useTranslation();
  const { formState, getField, updateFields, clearField } = useFormState(
    pick({ change_request }, fields).change_request
  );

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: props.appLogic.errors,
    formState,
    updateFields,
  });

  /* eslint-disable require-await */
  const handleSubmit = async () => {
    // Do nothing for now
  };

  // TODO(PORTAL-2064): Remove claimantShowModifications feature flag
  if (!isFeatureEnabled("claimantShowModifications")) return <PageNotFound />;

  return (
    <QuestionPage
      title={t("pages.claimsModifyType.title")}
      onSave={handleSubmit}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("change_request_type")}
        hint={t("pages.claimsModifyType.choiceHint")}
        choices={[
          {
            checked:
              formState.change_request_type === ChangeRequestType.modification,
            label: t("pages.claimsModifyType.modificationChoiceLabel"),
            value: ChangeRequestType.modification,
            hint: t("pages.claimsModifyType.modificationChoiceHint"),
          },
          {
            checked:
              formState.change_request_type === ChangeRequestType.withdrawal,
            label: t("pages.claimsModifyType.withdrawalChoiceText"),
            value: ChangeRequestType.withdrawal,
            hint: t("pages.claimsModifyType.withdrawalChoiceHint"),
          },
        ]}
        type="radio"
        label={t("pages.claimsModifyType.choiceLabel")}
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["end_date"]}
        getField={getField}
        updateFields={updateFields}
        clearField={clearField}
        visible={
          formState.change_request_type === ChangeRequestType.modification
        }
      >
        <Fieldset>
          <FormLabel
            component="legend"
            hint={
              <Trans
                i18nKey="pages.claimsModifyType.modificationLegendHint"
                components={{
                  "overpayments-link": (
                    <a
                      href={routes.external.massgov.overpayments}
                      rel="noreferrer noopener"
                      target="_blank"
                    />
                  ),
                }}
              />
            }
          >
            {t("pages.claimsModifyType.modificationLegend")}
          </FormLabel>
          <br />
          <ReviewRow
            noBorder
            level="3"
            label={t("pages.claimsModifyType.currentLeaveDatesLabel")}
          >
            {t("pages.claimsModifyType.currentLeaveDatesValue", {
              startDate: formatDate(claim_detail.startDate).short(),
              endDate: formatDate(claim_detail.endDate).short(),
            })}
          </ReviewRow>
          <InputDate
            {...getFunctionalInputProps("end_date")}
            label={t("pages.claimsModifyType.endDateLabel")}
            example={t("components.form.dateInputExample")}
            dayLabel={t("components.form.dateInputDayLabel")}
            monthLabel={t("components.form.dateInputMonthLabel")}
            yearLabel={t("components.form.dateInputYearLabel")}
            smallLabel
          />
        </Fieldset>
      </ConditionalContent>
    </QuestionPage>
  );
};

export default withUser(Type);
