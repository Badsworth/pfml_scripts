import { createStore } from "redux";
import reducers from "./reducers";

/**
 * The Redux "Store" is the object that brings our state management solution together. It:
 * - Holds our web application's state;
 * - Allows access to that state;
 * - Allows state to be updated via dispatch'ing actions
 * @see https://redux.js.org/basics/store
 * @returns {object}
 */
const initializeStore = (initialState = {}) =>
  createStore(
    reducers,
    initialState,
    global.__REDUX_DEVTOOLS_EXTENSION__ && global.__REDUX_DEVTOOLS_EXTENSION__()
  );

export default initializeStore;
