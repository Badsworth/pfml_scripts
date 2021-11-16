/**
 * Metadata for paginated collections. Includes info about the active page,
 * total pages, and ordering of the items on the page.
 */
interface PaginationMeta {
  page_offset: number;
  page_size: number;
  total_pages: number;
  total_records: number;
  order_by: string;
  order_direction: "ascending" | "descending";
}

export default PaginationMeta;
