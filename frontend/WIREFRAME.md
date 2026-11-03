# Plant page and passage highlight

Illustrative layout for one record. The same blocks are on the Archive plant page.

```text
+--------------------------------------------------+
| Medical warning                                  |
+--------------------------------------------------+
| sauge                                            |
| Candidate scientific name: Salvia officinalis L. |
| (a candidate, not a confirmed identification)    |
|                                                  |
| Extraction confidence 0.90 | Mapping: high       |
| Plant name: stated | Scientific name: inferred   |
|                                                  |
| Local name, part, preparation, described use     |
| Source MS Add. 9308 · folio 1r                   |
|                                                  |
| Original passage                                 |
| Take [sauge] and hony and sethe hem togidre.     |
|       ^^^^^ highlighted with the record span     |
+--------------------------------------------------+
```

The passage is split into three parts: before the span, the historical name, and after the span. Only the middle part is marked. When `span` is null, the whole passage stays unmarked and the plant evidence is shown as inferred.
