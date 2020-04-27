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
 * @param {saveFunction} saveToApi - Asynchronous function that saves the form state to the API
 * @param {Function} onSuccess - Success callback, called with the API result. Use for setting the React state to the response from the API
 * @returns {handleSave} Event handler that handles QuestionPage "save" events by saving the form state to the API and setting the state with the API response
 */
const useHandleSave = (saveToApi, onSuccess) => {
  /**
   * @param {object.<string, *>} formState Dictionary of form fields mapping names to values
   * @callback handleSave
   */
  const handleSave = async (formState) => {
    try {
      const result = await saveToApi(formState);

      if (result.success) {
        return onSuccess(result);
      }

      // TODO: Handle unsuccessful request (i.e response was a 4xx)
      // setErrors(...)
    } catch (error) {
      // TODO: Handle rejected promise (i.e unexpected error when props.onSubmit was called)
      // setErrors(...)
    }
  };
  return handleSave;
};

export default useHandleSave;
