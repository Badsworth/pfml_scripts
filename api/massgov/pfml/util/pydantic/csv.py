from typing import Any, Generic, Iterable, Type, TypeVar, Union

import pydantic

import massgov.pfml.util.csv as csv_util

_T = TypeVar("_T", bound=pydantic.BaseModel)


class DataWriter(csv_util.EncodingDictWriter, Generic[_T]):
    by_alias: bool

    def __init__(
        self, f: Any, row_type: Type[_T], by_alias: bool = True, *args: Any, **kwds: Any,
    ) -> None:
        self.by_alias = by_alias

        if by_alias:
            fieldnames = list(map(lambda f: f.alias, row_type.__fields__.values()))
        else:
            fieldnames = list(row_type.__fields__.keys())

        super().__init__(f, fieldnames, *args, **kwds)

    def _row_to_dict(self, row):
        return row if isinstance(row, dict) else row.dict(by_alias=self.by_alias)

    def writerow(self, rowdict: Union[_T, csv_util._DictRow]) -> Any:
        return super().writerow(self._row_to_dict(rowdict))

    def writerows(self, rowdicts: Iterable[Union[_T, csv_util._DictRow]]) -> Any:
        return super().writerows(map(self._row_to_dict, rowdicts))
