from collections import OrderedDict
import json


#### #### #### ####
#### class
#### #### #### ####
class DictHelper:
    STRING_ENCODING = "utf-8"

    @classmethod
    def to_bytes(cls, data: OrderedDict) -> bytes:
        return json.dumps(data).encode(cls.STRING_ENCODING)

    @classmethod
    def from_bytes(cls, data: bytes) -> OrderedDict:
        return json.loads(
            data.decode(cls.STRING_ENCODING), object_pairs_hook=OrderedDict
        )
