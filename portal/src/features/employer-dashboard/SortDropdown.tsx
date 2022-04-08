import Dropdown from "../../components/core/Dropdown";
import { GetClaimsParams } from "../../api/ClaimsApi";
import React from "react";
import { compact } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export interface PageQueryParam {
  name: string;
  value: number | null | string | string[];
}

interface SortDropdownProps
  extends Pick<GetClaimsParams, "order_by" | "order_direction"> {
  updatePageQuery: (params: PageQueryParam[]) => void;
}

export const SortDropdown = (props: SortDropdownProps) => {
  const { order_by, order_direction, updatePageQuery } = props;

  const choices = new Map([
    ["newest", "latest_follow_up_date,descending"],
    ["oldest", "latest_follow_up_date,ascending"],
    ["employee_az", "employee,ascending"],
    ["employee_za", "employee,descending"],
  ]);

  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    orderAndDirection: compact([order_by, order_direction]).join(","),
  });
  const getFunctionalInputProps = useFunctionalInputProps({
    formState,
    updateFields,
  });

  /**
   * Convert a selected dropdown option to order_by and order_direction params
   * @param orderAndDirection - comma-delineated order_by,order_direction
   */
  const getParamsFromOrderAndDirection = (orderAndDirection: string) => {
    const [order_by, order_direction] = orderAndDirection.split(",");

    return [
      {
        name: "order_by",
        value: order_by,
      },
      {
        name: "order_direction",
        value: order_direction,
      },
    ];
  };

  const handleChange = (evt: React.ChangeEvent<HTMLSelectElement>) => {
    updatePageQuery([
      ...getParamsFromOrderAndDirection(evt.target.value),
      {
        // Reset the page to 1 since ordering affects what shows on the first page
        name: "page_offset",
        value: "1",
      },
    ]);
  };

  return (
    <Dropdown
      {...getFunctionalInputProps("orderAndDirection")}
      onChange={handleChange}
      choices={Array.from(choices).map(([key, value]) => ({
        label: t<string>("pages.employersDashboard.sortChoice", {
          context: key,
        }),
        value,
      }))}
      label={t("pages.employersDashboard.sortLabel")}
      smallLabel
      formGroupClassName="display-flex margin-0 flex-align-center"
      labelClassName="text-bold margin-right-1"
      selectClassName="margin-0"
      hideEmptyChoice
    />
  );
};

export default SortDropdown;
