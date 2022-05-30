#!/usr/bin/env bash
set -euo pipefail

#
# Thin wrapper around rake search:catchup for cs_comment_service (forums).
#
# Reindexes documents created since WINDOW ago.
# If SLEEP_TIME is set to any number greater than 0, loops indefinitely. Since re-
# indexing can only yield correct results, the only risk of setting WINDOW too large
# is poor performance.
#
# Usage:
#  source ../forum_env; ./incremental-reindex.sh INDEX [WINDOW] [SLEEP_TIME] [BATCH_SIZE]
#
# Args:
#   INDEX       The index to re-index
#   WINDOW      Number of minutes ago to re-index from
#   SLEEP_TIME  Number of seconds to sleep between re-indexing
#   BATCH_SIZE  Number of documents to index per batch
#
# Example:
#   ./incremental-reindex.sh content 30
#

INDEX="$1"
WINDOW="${2:-5}"
SLEEP_TIME="${3:-60}"
BATCH_SIZE="${4:-500}"

if [ "$SLEEP_TIME" -ge "$((WINDOW * 60))" ]; then
  echo 'ERROR: SLEEP_TIME must not be longer than WINDOW, or else documents may be missed.'
  exit 1
fi

while : ; do
  echo "reindexing documents newer than $WINDOW minutes..."
  rake search:catchup["$WINDOW","$INDEX","$BATCH_SIZE"]
  echo "done. Sleeping $SLEEP_TIME seconds..."
  sleep "$SLEEP_TIME"

  [ "$SLEEP_TIME" -le 0 ] && break
done
