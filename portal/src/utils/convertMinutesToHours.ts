import { Integer } from "../../types/common";

/**
 * Convert minutes to object with hours and minutes
 */
const convertMinutesToHours = (minutes: Integer | null) => {
  return {
    hours: minutes === null ? 0 : Math.floor(minutes / 60),
    minutes: minutes === null ? 0 : minutes % 60,
  };
};

export default convertMinutesToHours;
