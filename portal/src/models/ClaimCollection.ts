import BaseCollection from "./BaseCollection";

export default class ClaimCollection extends BaseCollection {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'idProperty' in type 'ClaimCollection' is... Remove this comment to see the full error message
  get idProperty() {
    return "fineos_absence_id";
  }
}
