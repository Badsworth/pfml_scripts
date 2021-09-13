import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/router";
import useDebounce from "../hooks/useDebounce";
import isClient from "../utils/isClient";

export type Props = {
  search: (searchTerm: string) => Promise<unknown>;
  setResults: any; // @todo: better type?
  debounceDelay?: number;
};

const Search = ({ search, setResults, debounceDelay }: Props) => {
  const router = useRouter();
  const [isSearching, setIsSearching] = useState(false);

  const [searchTerm, setSearchTerm]: [string, any] = useState("");
  const debouncedSearchTerm = useDebounce(searchTerm, debounceDelay || 500);

  useEffect(() => {
    if (isClient() && router.query.search != null) {
      setSearchTerm(router.query.search);
    }
  }, [router.query.search]);

  useEffect(() => {
    if (debouncedSearchTerm) {
      setIsSearching(true);
      search(debouncedSearchTerm).then((results: unknown) => {
        setIsSearching(false);
        setResults(results);
      });
    } else {
      setIsSearching(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearchTerm]);

  const searchOnChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (isClient()) {
      localStorage.setItem("user-search-term", e.target.value);
    }
    setSearchTerm(e.target.value);
  };

  const searchOnSubmit = (e: FormEvent) => {
    e.preventDefault();
  };

  return (
    <form
      onSubmit={searchOnSubmit}
      className="search"
      data-testid="search-form"
    >
      <div className="search__input-wrapper">
        <input
          type="text"
          className="search__input"
          onChange={searchOnChange}
          placeholder="Enter email address"
          data-testid="search-input"
          value={searchTerm}
        />
        <i className="pfml-icon--search search__icon"></i>
      </div>
    </form>
  );
};

export default Search;
