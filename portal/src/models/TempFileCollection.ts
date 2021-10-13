import BaseCollection from "./BaseCollection";

export default class TempFileCollection extends BaseCollection {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'idProperty' in type 'TempFileCollection'... Remove this comment to see the full error message
  get idProperty() {
    return "id";
  }
}
