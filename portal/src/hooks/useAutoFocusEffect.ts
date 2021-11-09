import { RefObject, useEffect } from "react";

/**
 * React hook for automatically focusing on the first form element in the
 * amendment form when it is opened. This should only be used in components that utilize AmendmentForm.
 * @param params.containerRef - The container inside of which the amendment form exists.
 * @param params.isAmendmentFormDisplayed - Whether or not the amendment form is open.
 */
const useAutoFocusEffect = ({
  containerRef,
  isAmendmentFormDisplayed,
}: {
  containerRef: RefObject<HTMLElement>;
  isAmendmentFormDisplayed: boolean;
}) => {
  useEffect(() => {
    if (isAmendmentFormDisplayed && containerRef.current) {
      const amendmentForm =
        containerRef.current.querySelector(".c-amendment-form");
      const focusableElement = amendmentForm
        ? amendmentForm.querySelector("[tabIndex]:first-child, label")
        : null;
      if (focusableElement instanceof HTMLElement) focusableElement.focus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAmendmentFormDisplayed]);
};

export default useAutoFocusEffect;
