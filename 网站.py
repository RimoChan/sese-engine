from dataclasses import dataclass, field, asdict

from 存储 import 融合之门
from 配置 import 存储位置
from typing import MutableMapping, Dict, List, Any, Optional


网站信息 = 融合之门(存储位置/'网站之门')


@dataclass
class 网站:
    访问次数: int = 0
    最后访问时间: int = 0
    特征: Any = None
    成功率: Optional[float] = None
    结构: Optional[str] = None
    ip: Optional[List[str]] = None
    质量: Optional[float] = None
    https可用: Optional[bool] = None
    关键词: Optional[List[str]] = None
    链接: List[str] = field(default_factory=list)
    语种: Dict[str, float] = field(default_factory=dict)
    重定向: Dict[str, str] = field(default_factory=dict)
    服务器类型: List[str] = field(default_factory=list)


class _超网站信息(MutableMapping[str, 网站]):
    def __getitem__(self, k: str):
        d = 网站信息.get(k) or {}
        d = {k: v for k, v in d.items() if k in 网站.__dataclass_fields__ and v is not None}
        return 网站(**d)

    def __setitem__(self, k: str, v:网站):
        网站信息[k] = asdict(v)

    __iter__ = __len__ = __delitem__ = lambda: 0/0


超网站信息 = _超网站信息()
