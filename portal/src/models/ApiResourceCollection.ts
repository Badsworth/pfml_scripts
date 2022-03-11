export interface ApiResource {
  // API resources are expected to be objects. We expect at least an ID property.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

/**
 * Readonly generic class representing a collection of a specific data model. Methods
 * return new instances of the collection rather than modifying the original collection.
 * @example const c = new ApiResourceCollection<Document>("document_id", [{ document_id: "123", name: "example" }]);
 *          c.setItem({ document_id: "456", name: "example2" });
 */
class ApiResourceCollection<TApiResource extends ApiResource> {
  idKey: keyof TApiResource;
  private map: Map<string, TApiResource>;

  constructor(idKey: keyof TApiResource, items: TApiResource[] = []) {
    this.idKey = idKey;
    this.map = new Map(
      items.map((item) => {
        return [item[idKey], item];
      })
    );
  }

  private get _mutableMap() {
    return new Map(this.map);
  }

  private _arrayFromMap(map: Map<string, TApiResource>): TApiResource[] {
    return Array.from(map.values());
  }

  get items(): TApiResource[] {
    return this._arrayFromMap(this.map);
  }

  get isEmpty(): boolean {
    return this.map.size === 0;
  }

  getItem(itemId: string): TApiResource | undefined {
    return this.map.get(itemId);
  }

  /**
   * Add or update an item in the collection. Returns a new collection with the
   * item included. Does not modify the original collection.
   */
  setItem(item: TApiResource): ApiResourceCollection<TApiResource> {
    const updatedMap = this._mutableMap.set(item[this.idKey], item);
    return new ApiResourceCollection<TApiResource>(
      this.idKey,
      this._arrayFromMap(updatedMap)
    );
  }

  /**
   * Add or update items in the collection. Returns a new collection with the
   * items included. Does not modify the original collection.
   */
  setItems(items: TApiResource[] = []): ApiResourceCollection<TApiResource> {
    const updatedMap = this._mutableMap;
    items.forEach((item) => {
      updatedMap.set(item[this.idKey], item);
    });
    return new ApiResourceCollection<TApiResource>(
      this.idKey,
      this._arrayFromMap(updatedMap)
    );
  }

  /**
   * Removes an item from the collection. Returns a new collection with the item removed.
   * Does not modify the original collection.
   */
  removeItem(itemId: string): ApiResourceCollection<TApiResource> {
    const updatedMap = this._mutableMap;
    updatedMap.delete(itemId);

    return new ApiResourceCollection<TApiResource>(
      this.idKey,
      this._arrayFromMap(updatedMap)
    );
  }
}

export default ApiResourceCollection;
