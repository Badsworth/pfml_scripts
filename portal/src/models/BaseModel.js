import { isEqual, merge } from "lodash";

/**
 * Class representing the base class for the application's models
 */
export default class BaseModel {
  /**
   * Create an object from a dictionary of attributes and initializes the object with it,
   * only setting attributes that the model class has.
   * @param {object.<string, *>} attrs Object of attributes, where keys are the attribute names and the values are the attribute values
   */
  constructor(attrs) {
    attrs = attrs || {};

    for (const [property, defaultValue] of Object.entries(this.defaults)) {
      this[property] = defaultValue;
    }

    for (const [property, value] of Object.entries(attrs)) {
      // Ignore top-level attributes that aren't part of the model class's defaults array
      if (!this.defaults.hasOwnProperty(property)) {
        // Log a warning since it might indicate a missing field on the model or API, indicating a potential bug.
        // TODO (CP-694): Don't log a warning when the field is a temporary field, in which case it's expected that this field doesn't exist in the API yet
        // eslint-disable-next-line no-console
        console.warn(
          'Received unexpected attribute: "%s"\nThe model may need updated if this is a new field.',
          property
        );

        continue;
      }

      merge(this, { [property]: value });
    }
  }

  /**
   * Dictionary mapping properties to default values for those properties.
   * If a property has no default, use null as its default.
   * This is an abstract method that must be implemented by all subclasses of BaseModel.
   * @type {object.<string, *>}
   * @readonly
   * @abstract
   */
  get defaults() {
    throw new Error("Not implemented");
  }

  /**
   * Check to see if this object is set to the default values
   * @returns {boolean} true if this object has default values and false otherwise
   */
  isDefault() {
    return isEqual(this, new this.constructor());
  }
}
