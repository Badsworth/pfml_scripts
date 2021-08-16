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
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'page_offset' does not exist on type 'Pag... Remove this comment to see the full error message
    this.page_offset = pagingMeta.page_offset;
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'page_size' does not exist on type 'Pagin... Remove this comment to see the full error message
    this.page_size = pagingMeta.page_size;
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'total_pages' does not exist on type 'Pag... Remove this comment to see the full error message
    this.total_pages = pagingMeta.total_pages;
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'total_records' does not exist on type 'P... Remove this comment to see the full error message
    this.total_records = pagingMeta.total_records;
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'order_by' does not exist on type 'Pagina... Remove this comment to see the full error message
    this.order_by = pagingMeta.order_by;
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'order_direction' does not exist on type ... Remove this comment to see the full error message
    this.order_direction = pagingMeta.order_direction;
  }
}

export default PaginationMeta;
