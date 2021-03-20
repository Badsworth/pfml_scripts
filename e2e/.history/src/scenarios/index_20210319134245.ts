/**
 * All Scenarios are exported from this file.
 *
 * They can be included like:
 * include * as scenarios from "../scenarios";
 *
 * Because scenarios are simple data objects, we only need to include them if we're going to want to reuse them
 * frequently (eg: in Cypress tests). Not every scenario we do data generation for needs to be added to our master
 * library.
 */
export * from "./cypress";
export * from "./2021-03-11-training";
export * from "./UAT";
