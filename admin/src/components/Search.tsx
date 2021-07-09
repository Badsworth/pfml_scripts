import {
  useState,
  useEffect,
  Dispatch,
  ChangeEvent,
  SetStateAction,
} from "react";
import useDebounce from "../hooks/useDebounce";

type Props = {
  search: (searchTerm: string) => Promise<unknown>;
  setResults: any;
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
      // setResults([]);
      setIsSearching(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearchTerm]);

  const searchOnChange = (e: ChangeEvent<HTMLInputElement>) =>
    setSearchTerm(e.target.value);

  return (
    <div className="search">
      <form className="search__form">
        <input
          type="text"
          className="search__input"
          onChange={searchOnChange}
        />
      </form>
    </div>
  );
};

export default Search;
