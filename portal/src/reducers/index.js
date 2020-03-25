/*
 * @file Redux Reducers and Selectors.
 * A “reducer” specifies how the application's state changes in
 * response to actions sent to the store. A reducer is a pure
 * function that takes the previous state and an action, and
 * returns the next state.
 * @see https://redux.js.org/basics/reducers
 */
import { combineReducers } from "redux";
import form from "./form";

/**
 * This is our top-level reducer for all of our site's state. This
 * is the reducer that gets passed into our Redux store and all
 * actions routed through.
 */
const reducer = combineReducers({ form });
export default reducer;
