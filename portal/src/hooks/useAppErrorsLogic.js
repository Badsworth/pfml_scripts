import AppErrorInfo from "../models/AppErrorInfo";
import AppErrorInfoCollection from "../models/AppErrorInfoCollection";
import tracker from "../services/tracker";
import useCollectionState from "./useCollectionState";
import { useTranslation } from "../locales/i18n";

const useAppErrorsLogic = () => {
  const { t } = useTranslation();

  /**
   * State representing both application errors and
   * validation errors
   */
  const {
    collection: appErrors,
    setCollection: setAppErrors,
  } = useCollectionState(() => new AppErrorInfoCollection());

  /**
   * Catch errors from generic try / catch blocks around API calls
   * @param {Error} error - JS Error object
   */
  const catchError = (error) => {
    console.error(error);

    const appError = new AppErrorInfo({
      type: error.name,
      message:
        error.name === "NetworkError" ? t("errors.network") : error.message,
    });

    setAppErrors(new AppErrorInfoCollection([appError]));

    tracker.noticeError(error);
  };

  /**
   * Convenience method for setting errors to null
   */
  const clearErrors = () => {
    setAppErrors(null);
  };

  return {
    appErrors,
    setAppErrors,
    catchError,
    clearErrors,
  };
};

export default useAppErrorsLogic;
