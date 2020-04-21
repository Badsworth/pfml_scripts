/**
 * @callback saveFunction
 * @param {object.<string, *>} formState Dictionary of form fields mapping names to values
 * @returns {Promise<BaseModel>} Promise resolving to a model that represents the API response
 */

/**
 * React hook that connects the behavior of API functions that save data to the API and
 * React state functions that set the application state. It takes the API save function and the React setState
 * functions as parameters and returns an onSave handler that can be used to handle the QuestionPage
 * onSave event. Eventually this function will also handle errors that can happen during save.
 *
 * @param {saveFunction} saveToApi Asynchronous function that saves the form state to the API
 * @param {Function} setState Function that sets the React state to the response from the API
 * @returns {handleSaveFunction} Event handler that handles QuestionPage "save" events by saving the form state to the API and setting the state with the API response
 */
const useHandleSave = (saveToApi, setState) => {
  /**
   * @callback handleSaveFunction
   * @param {object.<string, *>} formState Dictionary of form fields mapping names to values
   */
  const handleSave = async (formState) => {
    const result = await saveToApi(formState);
    setState(result);
  };
  return handleSave;
};

export default useHandleSave;
