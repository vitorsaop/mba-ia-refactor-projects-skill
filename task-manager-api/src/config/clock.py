"""Fonte de tempo, T14.

`datetime.utcnow()` está depreciado desde Python 3.12. O substituto oficial
devolve valor com fuso, enquanto as colunas deste projeto persistem valor sem
fuso. `replace(tzinfo=None)` preserva exatamente o valor anterior e remove o
símbolo obsoleto.
"""
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
