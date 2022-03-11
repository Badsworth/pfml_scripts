import { ErrorsLogic } from "./useErrorsLogic";
import { Holiday } from "../models/Holiday";
import HolidaysApi from "../api/HolidaysApi";
import { useState } from "react";

const useHolidaysLogic = ({ errorsLogic }: { errorsLogic: ErrorsLogic }) => {
  const holidaysApi = new HolidaysApi();

  const [holidays, setHolidays] = useState<Holiday[]>();
  const [isLoadingHolidays, setIsLoadingHolidays] = useState<boolean>();
  const hasLoadedHolidays = !!holidays;

  // Load holidays from API
  const loadHolidays = async (startDate: string, endDate: string) => {
    if (isLoadingHolidays) return;
    if (hasLoadedHolidays) return;

    setIsLoadingHolidays(true);
    errorsLogic.clearErrors();
    try {
      const holidays = await holidaysApi.getHolidays(startDate, endDate);
      setHolidays(holidays);
    } catch (error) {
      errorsLogic.catchError(error);
    } finally {
      setIsLoadingHolidays(false);
    }
  };

  return {
    loadHolidays,
    holidays,
    hasLoadedHolidays,
    isLoadingHolidays,
  };
};

export default useHolidaysLogic;
export type HolidaysLogic = ReturnType<typeof useHolidaysLogic>;
