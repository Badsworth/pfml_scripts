import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import useDebounce from "../hooks/useDebounce";

type Props = {
  search: (searchTerm: string) => Promise<unknown>;
  setResults: any; // @todo: better type?
  debounceDelay?: number;
};

const Search = ({ search, setResults, debounceDelay }: Props) => {
  const [isSearching, setIsSearching] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearchTerm = useDebounce(searchTerm, debounceDelay || 500);

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
    setSearchTerm(e.target.value);
  };

  const searchOnSubmit = (e: FormEvent) => {
    e.preventDefault();
  };

  return (
    <form onSubmit={searchOnSubmit} className="search">
      <div className="search__input-wrapper">
        <input
          type="text"
          className="hasIcon--left"
          onChange={searchOnChange}
          placeholder="Enter email address"
        />
        <i className="pfml-icon--search search__icon"></i>
      </div>
    </form>
  );
};

export default Search;
