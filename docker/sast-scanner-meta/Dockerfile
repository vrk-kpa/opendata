FROM 373155601093.dkr.ecr.eu-west-1.amazonaws.com/dvv/sast-scanner-meta:v1.0.0

COPY ./entrypoint.sh /app/
RUN ["chmod", "+x", "/app/entrypoint.sh"]

WORKDIR /src

ENTRYPOINT ["sh", "-c", "/app/entrypoint.sh ${LEVEL} ${TARGET} ${SRCDIR} ${IACDIR} ${OUTDIR} ${FORMAT} ${EXCLUDE_RULES}"]
