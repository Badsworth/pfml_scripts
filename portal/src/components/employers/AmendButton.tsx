import Button from "../Button";
import Icon from "../Icon";
import React from "react";
import { useTranslation } from "../../locales/i18n";

interface AmendButtonProps {
  onClick?: (...args: any[]) => any;
}

/**
 * Link with edit icon for amendable sections
 * in the Leave Admin claim review page.
 */
const AmendButton = ({ onClick }: AmendButtonProps) => {
  const { t } = useTranslation();

  return (
    <Button
      className="text-no-wrap"
      variation="unstyled"
      onClick={onClick}
      data-test="amend-button"
    >
      <Icon
        name="edit"
        className="text-middle margin-right-05 margin-top-neg-05"
      />
      {t("components.amendButton.amend")}
    </Button>
  );
};

export default AmendButton;
