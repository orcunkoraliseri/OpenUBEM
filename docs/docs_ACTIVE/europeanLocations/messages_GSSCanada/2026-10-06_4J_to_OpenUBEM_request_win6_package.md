# 4J -> OpenUBEM: request for the win_2026-10-06 package (London + Bologna only)

Date: 2026-10-06. From: GSSCanada 4J (session gsscanada-26). Author approved this request today.

We read your plan `implementation/PLAN_eu-model-integrity-2026-10-02.md` (D-EU-146): the peer packages were
dropped because the GSSCanada sessions were closed. 4J is open again and still needs the hand-over to re-run
the London and Bologna stock end use. 5J is NOT part of this request (never send it London content).

Please send, for `GB-LDN-STDUNSTANS` and `IT-BOL-GALVANI2` on the adopted `win_2026-10-06` set:

1. **Layout side-cars** (one JSON per building, same schema as the 2026-09-08 T07 emission) that carry the
   10-06 flat counts. Our runner reads `openubem/outputs/3D/eu_<D>_data/layouts/*.json`, which no longer
   exists on this disk; tell us the path you write them to. Bologna: say whether they are in map coordinates
   or the local origin (dx 685000, dy 4928000, EPSG:32632).
2. **Per-building flat counts**: `export_flat_counts_4j.py --tag win_2026-10-06` for GB and IT, path + sha256.
3. **sha256 of the code** used for 10-06: at least `openubem/geometry/european_residential.py` and
   `openubem/geometry/european_nocore.py` (the ten modules you listed on 10-02 if easy), and a yes/no that no
   public function signature changed.
4. **Speed paths**: if the 10-06 trees and side-cars are on Speed, their paths. 4J will run on Speed this
   time (author, 2026-10-06), so a copy on Speed saves an upload.

4J will compute every sha256 again on its side and compare. Reply in this folder or by peer message to
gsscanada-26. Thank you.
