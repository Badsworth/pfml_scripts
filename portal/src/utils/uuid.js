/**
 * method that returns random uuidv4
 * this is a temporary function for use in mocking API response
 * TODO: remove this function and all references to it once all API mocks are
 * ready
 * @see https://stackoverflow.com/questions/105034/how-to-create-guid-uuid
 * @returns {string} - uuidv4 string
 */
export default () => {
  let dt = new Date().getTime();
  const uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
    /[xy]/g,
    function (c) {
      const r = (dt + Math.random() * 16) % 16 | 0;
      dt = Math.floor(dt / 16);
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    }
  );
  return uuid;
};
