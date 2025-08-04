#!/bin/bash

EXCLUSIONS="README.md,LICENSE.md,web/coverage,web/node,web/node_properties,application.properties"
EXCLUDES=""
IFS=',' read -ra ADDR <<< "$EXCLUSIONS"
for i in "${ADDR[@]}"; do
    EXCLUDES+="--exclude $i "
done

echo "[*] using exclude for files ${EXCLUSIONS}"

RULE_EXCLUSIONS="--exclude-rule python.lang.compatibility.python37.python37-compatibility-importlib2 "
IFS=',' read -ra ADDR <<< "$EXCLUDE_RULES"
for i in "${ADDR[@]}"; do
    RULE_EXCLUSIONS+="--exclude-rule $i "
done

echo "[*] using exclude for rules ${RULE_EXCLUSIONS}"

APP_RULES="--config /app/custom-rules --config "p/default" --config "p/ci" --config "p/java" --config "p/python" --config "p/docker" --config "p/typescript" --config "p/javascript" --config "p/kotlin"  --config "p/r2c-security-audit" --config "p/eslint" --config "p/csharp""

IAC_RULES="--config /app/custom-rules --config "p/terraform" --config "p/kubernetes""

function summary {
  function join_by { local IFS="$1"; shift; echo "$*"; }
  sarif summary $2 | grep -v '^\s' | grep .
  SUMMARIES=($(sarif summary $2  | grep -v '^\s' | grep . | tr -d " "))
  SEVERITIES=()
  SEVERITY_COUNTS=()
  for summary in "${SUMMARIES[@]}"
  do
    SEVERITIES+=("$(echo $summary | cut -d':' -f1)")
    SEVERITY_COUNTS+=("$(echo $summary | cut -d':' -f2)")
  done
  summary_file=$1
  join_by , "${SEVERITIES[@]}" > $summary_file
  join_by , "${SEVERITY_COUNTS[@]}" >> $summary_file

  echo "[*] Summary report written to $1"
}

handle_output() {
  if [ -f $OUTDIR/semgrep-app-report.sarif ]; then
    sarif html $OUTDIR/semgrep-app-report.sarif --output $OUTDIR/semgrep-app-report-from-sarif.html
    summary "$OUTDIR/semgrep-app-summary.csv" "$OUTDIR/semgrep-app-report.sarif"
    echo "[*] HTML scan app results written"
  fi

  if [ -f $OUTDIR/semgrep-iac-report.sarif ]; then
    sarif html $OUTDIR/semgrep-iac-report.sarif --output $OUTDIR/semgrep-app-report-from-sarif.html
    summary "$OUTDIR/semgrep-iac-summary.csv" "$OUTDIR/semgrep-iac-report.sarif"

    echo "[*] HTML scan iac results written"
  fi

  if [ -f $OUTDIR/semgrep-app-report.xml ]; then
    mv $OUTDIR/semgrep-app-report.xml $OUTDIR/semgrep-app-junit-report.xml
    echo "[*] XML scan app results written"

    junit2html $OUTDIR/semgrep-app-junit-report.xml $OUTDIR/semgrep-app-report.html
    echo "[*] HTML scan app results written"
  fi

  if [ -f $OUTDIR/semgrep-iac-report.xml ]; then
    mv $OUTDIR/semgrep-iac-report.xml $OUTDIR/semgrep-iac-junit-report.xml
    echo "[*] XML scan iac results written"

    junit2html $OUTDIR/semgrep-iac-junit-report.xml $OUTDIR/semgrep-iac-report.html
    echo "[*] HTML scan iac results written"
  fi
}

# Handling severity levels
if [ $# -eq 0 ]
  then
    echo "[*] Default severity levels will be used."
    SEMGREP_SEVERITY="--severity ERROR"
elif [ $1 = "LOW" ]
  then
    echo "[*] Custom LOW severity levels will be used."
    SEMGREP_SEVERITY="--severity INFO"
elif [ $1 = "MEDIUM" ]
  then
    echo "[*] Custom MEDIUM severity levels will be used."
    SEMGREP_SEVERITY="--severity WARNING"
elif [ $1 = "HIGH" ]
  then
    echo "[*] Custom HIGH severity levels will be used."
    SEMGREP_SEVERITY="--severity ERROR"
elif [ $1 = "CRITICAL" ]
  then
    echo "[*] Custom CRITICAL severity levels will be used."
    SEMGREP_SEVERITY="--severity ERROR"
elif [ $1 = "ALL" ]
  then
    echo "[*] Custom ALL severity levels will be used."
    SEMGREP_SEVERITY=""
else
  echo "[x] Invalid severity level. Default severity levels will be used."
  SEMGREP_SEVERITY="--severity ERROR"
fi


run_semgrep() {
  echo "[*] Running semgrep on $1 source in $2"
  if [ $FORMAT = "sarif" ]
    then
      echo "[*] SARIF format will be used."
      OUTPUT_ARGS="--sarif --sarif-output $OUTDIR/semgrep-$1-report.sarif"
  else
    echo "[*] JUNIT-XML format will be used."
    OUTPUT_ARGS="--junit-xml --output $OUTDIR/semgrep-$1-report.xml"
  fi
  semgrep ci $3 --metrics=off $EXCLUDES $RULE_EXCLUSIONS $OUTPUT_ARGS --no-suppress-errors $ARGS
}

if [ $2 = "APP" ]
  then
    run_semgrep "app" $SRCDIR "$APP_RULES"

    handle_output
elif [ $2 = "IAC" ]
  then
    run_semgrep "iac" $IACDIR "$IAC_RULES"
    handle_output
else
  run_semgrep "app" $SRCDIR "$APP_RULES"
  run_semgrep "iac" $IACDIR "$IAC_RULES"

  handle_output
fi

if [[ "${BUCKET}" ]]; then
  /copy_to_s3.sh
fi

echo "[*] All done!"
exit 0
