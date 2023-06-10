import copy
import json
import math
import os

from rapidfuzz import fuzz


class DirectoryHandler:
    METADATA_SUBDIRECTORY = ".metadata"

    def __init__(self, directory: str):
        self._directory = directory
        os.makedirs(self._directory, exist_ok=True)
        os.makedirs(
            os.path.join(self._directory, self.METADATA_SUBDIRECTORY),
            exist_ok=True,
        )
        self._files = set(
            f
            for f in os.listdir(self._directory)
            if os.path.isfile(os.path.join(self._directory, f))
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({json.dumps(self.__dict__)})"

    def __contains__(self, file_name: str) -> bool:
        return self.file_exists(file_name=file_name)

    @property
    def directory(self) -> str:
        return self._directory

    def file_exists(self, file_name: str) -> bool:
        return file_name in self._files

    def write_to_file(self, file_name: str, data: bytes):
        self._files.add(file_name)
        with open(os.path.join(self._directory, file_name), "wb") as f:
            f.write(data)

    def read_from_file(self, file_name: str) -> bytes:
        self._assert_file_exists(file_name)
        with open(os.path.join(self._directory, file_name), "rb") as f:
            return f.read()

    def delete_file(self, file_name: str):
        self._assert_file_exists(file_name)
        fpath = os.path.join(self._directory, file_name)
        os.remove(fpath)
        self._files.remove(file_name)

    def get_all_files_name(self) -> set:
        return copy.deepcopy(self._files)

    def write_metadata(self, file_name: str, data: bytes):
        open(
            os.path.join(
                self._directory,
                self.METADATA_SUBDIRECTORY,
                file_name,
            ),
            "wb",
        ).write(data)

    def read_metadata(self, file_name: str) -> bytes | None:
        try:
            return open(
                os.path.join(
                    self._directory,
                    self.METADATA_SUBDIRECTORY,
                    file_name,
                ),
                "rb",
            ).read()
        except FileNotFoundError:
            return None

    def search_file_name(
        self, target_name: str, n_candidates: int = 9
    ) -> list:
        name_and_score = [
            (f, fuzz.ratio(target_name, f, processor=str.lower))
            for f in self._files
        ]
        name_and_score = [
            i for i in name_and_score if not math.isclose(i[1], 0)
        ]
        candidates = [i for i in name_and_score if math.isclose(i[1], 100)]
        name_and_score = [
            i for i in name_and_score if not math.isclose(i[1], 100)
        ]
        while len(candidates) < n_candidates and len(name_and_score) > 0:
            next_candidate = max(name_and_score, key=lambda x: x[1])
            name_and_score.remove(next_candidate)
            candidates.append(next_candidate)
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [i[0] for i in candidates]

    def _assert_file_exists(self, file_name: str):
        assert self.file_exists(file_name), f"File {file_name} does not exist"
