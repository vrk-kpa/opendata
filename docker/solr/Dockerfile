FROM solr:9.8.0

# switch from solr to root user
USER root

# upgrade system
RUN apt-get update -yq && apt-get upgrade -yq

# setup env vars
ENV SOLR_CORE=ckan
ENV SOLR_CORE_PATH=/var/solr/data

# create folders
RUN mkdir -p $SOLR_CORE_PATH/$SOLR_CORE/conf
RUN mkdir -p $SOLR_CORE_PATH/$SOLR_CORE/data

# add config files
COPY solrconfig.xml $SOLR_CORE_PATH/$SOLR_CORE/conf/
COPY schema.xml $SOLR_CORE_PATH/$SOLR_CORE/conf/
RUN cp /opt/solr/server/solr/configsets/sample_techproducts_configs/conf/currency.xml \
       /opt/solr/server/solr/configsets/_default/conf/synonyms.txt \
       /opt/solr/server/solr/configsets/_default/conf/stopwords.txt \
       /opt/solr/server/solr/configsets/_default/conf/protwords.txt \
       /opt/solr/server/solr/configsets/sample_techproducts_configs/conf/elevate.xml \
       $SOLR_CORE_PATH/$SOLR_CORE/conf/

# create core.properties
RUN echo name=$SOLR_CORE > $SOLR_CORE_PATH/$SOLR_CORE/core.properties

# setup permissions
RUN chown -R "$SOLR_USER:$SOLR_USER" $SOLR_CORE_PATH/$SOLR_CORE

# switch from root to solr user
USER $SOLR_USER:$SOLR_USER
