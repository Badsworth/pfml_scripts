import { Integer } from "../../types/common";

/**
 * Convert minutes to object with hours and minutes
 */
const convertMinutesToHours = (minutes: Integer | null) => {
  return {
    hours: minutes ? Math.floor(minutes / 60) : 0,
    minutes: minutes ? minutes % 60 : 0,
  };
};

export default convertMinutesToHours;
