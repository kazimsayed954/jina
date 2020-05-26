__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import random
from typing import Iterator, Union

from ...logging import default_logger

from ...enums import ClientInputType, ClientMode
from ...helper import batch_iterator
from ...proto import jina_pb2


def _generate(data: Union[Iterator[bytes], Iterator['jina_pb2.Document'], Iterator[str]], batch_size: int = 0,
              first_doc_id: int = 0, first_request_id: int = 0,
              random_doc_id: bool = False, mode: ClientMode = ClientMode.INDEX, top_k: int = 50,
              input_type: ClientInputType = ClientInputType.BUFFER,
              mime_type: str = None,
              *args, **kwargs) -> Iterator['jina_pb2.Message']:
    if isinstance(mode, str):
        mode = ClientMode.from_string(mode)

    for pi in batch_iterator(data, batch_size):
        req = jina_pb2.Request()
        req.request_id = first_request_id

        if mode == ClientMode.SEARCH:
            if top_k <= 0:
                raise ValueError('"top_k: %d" is not a valid number' % top_k)
            else:
                req.search.top_k = top_k

        for _raw in pi:
            d = getattr(req, str(mode).lower()).docs.add()
            if input_type == ClientInputType.PROTOBUF:
                d.CopyFrom(_raw)
            elif input_type == ClientInputType.DATA_URI:
                d.data_uri = _raw
            elif input_type == ClientInputType.FILE_PATH:
                d.file_path = _raw
            elif input_type == ClientInputType.BUFFER:
                if isinstance(_raw, str):
                    _raw = _raw.encode()  # auto-fix for str
                d.buffer = _raw
                if not mime_type:
                    default_logger.warning('starting from v0.2.0, '
                                           'the best practice of sending binary data is with "mime_type". '
                                           'when not given then MIME sniff (based on libmagic) will be used')
            d.doc_id = first_doc_id if not random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
            d.weight = 1.0
            first_doc_id += 1
        yield req
        first_request_id += 1


def index(*args, **kwargs):
    """Generate indexing request"""
    yield from _generate(*args, **kwargs)


def train(*args, **kwargs):
    """Generate training request """
    yield from _generate(*args, **kwargs)
    req = jina_pb2.Request()
    req.request_id = 1
    req.train.flush = True
    yield req


def search(*args, **kwargs):
    """Generate search request """
    yield from _generate(*args, **kwargs)
