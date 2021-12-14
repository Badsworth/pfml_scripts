const mockFetch = ({
  response = { data: {}, errors: {}, warnings: [] },
  ok = true,
  status = 200,
  headers = [],
}: {
  response: Record<string, unknown>;
  ok?: boolean;
  status?: number;
  headers?: object;
}) => {
  return jest.fn().mockResolvedValueOnce({
    ...response,
    ok,
    status,
    headers,
  });
};

export default mockFetch;
