import { createStore } from "redux";
import reducers from "./reducers";

/**
 * The Redux "Store" is the object that brings our state management solution together. It:
 * - Holds our web application's state;
 * - Allows access to that state;
 * - Allows state to be updated via dispatch'ing actions
 * @see https://redux.js.org/basics/store
 * @param {object} initialState - initial state of redux store
 * @returns {object} redux store
 */
export const initializeStore = (initialState = {}) =>
  createStore(
    reducers,
    initialState,
    global.__REDUX_DEVTOOLS_EXTENSION__ && global.__REDUX_DEVTOOLS_EXTENSION__()
  );

let store;
/**
 * Initialize redux store inside functional component
 * @returns {object} redux store
 */
export const useStore = (initialState = {}) => {
  store = store || initializeStore(initialState);
  return store;
};
