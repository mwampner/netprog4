from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Node(_message.Message):
    __slots__ = ["id", "port", "address"]
    ID_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    id: int
    port: int
    address: str
    def __init__(self, id: _Optional[int] = ..., port: _Optional[int] = ..., address: _Optional[str] = ...) -> None: ...

class NodeList(_message.Message):
    __slots__ = ["responding_node", "nodes"]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    NODES_FIELD_NUMBER: _ClassVar[int]
    responding_node: Node
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    def __init__(self, responding_node: _Optional[_Union[Node, _Mapping]] = ..., nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ...) -> None: ...

class IDKey(_message.Message):
    __slots__ = ["node", "idkey"]
    NODE_FIELD_NUMBER: _ClassVar[int]
    IDKEY_FIELD_NUMBER: _ClassVar[int]
    node: Node
    idkey: int
    def __init__(self, node: _Optional[_Union[Node, _Mapping]] = ..., idkey: _Optional[int] = ...) -> None: ...

class KeyValue(_message.Message):
    __slots__ = ["node", "key", "value"]
    NODE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    node: Node
    key: int
    value: str
    def __init__(self, node: _Optional[_Union[Node, _Mapping]] = ..., key: _Optional[int] = ..., value: _Optional[str] = ...) -> None: ...

class KV_Node_Wrapper(_message.Message):
    __slots__ = ["responding_node", "mode_kv", "kv", "nodes"]
    RESPONDING_NODE_FIELD_NUMBER: _ClassVar[int]
    MODE_KV_FIELD_NUMBER: _ClassVar[int]
    KV_FIELD_NUMBER: _ClassVar[int]
    NODES_FIELD_NUMBER: _ClassVar[int]
    responding_node: Node
    mode_kv: bool
    kv: KeyValue
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    def __init__(self, responding_node: _Optional[_Union[Node, _Mapping]] = ..., mode_kv: bool = ..., kv: _Optional[_Union[KeyValue, _Mapping]] = ..., nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ...) -> None: ...
