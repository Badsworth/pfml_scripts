/**
 * Convert minutes to object with hours and minutes
 * @param {number} minutes - minutes, must be an integer
 * @returns {{ hours, minutes }}
 */
const convertMinutesToHours = (minutes) => {
  return {
    hours: Math.floor(minutes / 60),
    minutes: minutes % 60,
  };
};

export default convertMinutesToHours;
