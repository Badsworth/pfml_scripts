import Collection from "./Collection";
import { keyBy } from "lodash";

export default class ClaimCollection extends Collection {
  /**
   * Construct an instance of ClaimCollection
   * @param {Claim[]} claims Array of claims
   */
  constructor(claims) {
    const idProperty = "application_id";
    const itemsById = keyBy(claims, idProperty);
    super({ idProperty, itemsById });
  }
}
