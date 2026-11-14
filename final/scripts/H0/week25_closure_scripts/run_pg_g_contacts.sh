#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_g_contacts.exit' EXIT
for variant in g baseline; do
  odb='/runtime_final/pg_compact_g.odb'
  if [ "$variant" = baseline ]; then odb='/runtime/F.odb'; fi
  docker run --rm --name "faultv-w25-pg-$variant-contacts-export" --user 1000:1000 --memory=2500m --cpus=1 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/export_pg_contact_geometry.py "$odb" "reports/pg_${variant}_contact_geometry.json" > "logs/pg_${variant}_contact_export.log" 2>&1
  docker run --rm --name "faultv-w25-pg-$variant-contacts" --user 1000:1000 --memory=2500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/audit_pg_contacts.py "reports/pg_${variant}_contact_geometry.json" "reports/pg_${variant}_contacts.json" > "logs/pg_${variant}_contacts.log" 2>&1
done
