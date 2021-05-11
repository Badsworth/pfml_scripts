/**
 * Metadata for paginated collections. Includes info about the active page,
 * total pages, and ordering of the items on the page.
 */
class PaginationMeta {
  /**
   * @param {object} [pagingMeta] - API response body's `meta.paging` object
   * @param {number} pagingMeta.page_offset
   * @param {number} pagingMeta.page_size
   * @param {number} pagingMeta.total_pages
   * @param {number} pagingMeta.total_records
   * @param {string} pagingMeta.order_by
   * @param {string} pagingMeta.order_direction
   */
  constructor(pagingMeta = {}) {
    this.page_offset = pagingMeta.page_offset;
    this.page_size = pagingMeta.page_size;
    this.total_pages = pagingMeta.total_pages;
    this.total_records = pagingMeta.total_records;
    this.order_by = pagingMeta.order_by;
    this.order_direction = pagingMeta.order_direction;
  }
}

export default PaginationMeta;
