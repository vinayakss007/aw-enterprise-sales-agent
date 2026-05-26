import { useState } from 'react';

export function usePagination(initialLimit = 20) {
  const [page, setPage] = useState(0);
  const [limit] = useState(initialLimit);
  const skip = page * limit;
  return { page, setPage, limit, skip, hasNext: (totalLoaded: number) => totalLoaded === limit };
}
