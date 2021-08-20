import { useEffect } from "react";

/**
 * React hook for automatically focusing on the first form element in the
 * amendment form when it is opened. This should only be used in components that utilize AmendmentForm.
 * @param {Object} params - The parameters required for the correct form elements to auto-focus.
 * @param {import("react").RefObject} params.containerRef - The container inside of which the amendment form exists.
 * @param {boolean} params.isAmendmentFormDisplayed - Whether or not the amendment form is open.
 */
const useAutoFocusEffect = ({ containerRef, isAmendmentFormDisplayed }) => {
  useEffect(() => {
    if (containerRef && isAmendmentFormDisplayed) {
      const amendmentForm =
        containerRef.current.querySelector(".c-amendment-form");
      const focusableElement = amendmentForm.querySelector(
        "[tabIndex]:first-child, label"
      );
      if (focusableElement) focusableElement.focus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAmendmentFormDisplayed]);
};

export default useAutoFocusEffect;
