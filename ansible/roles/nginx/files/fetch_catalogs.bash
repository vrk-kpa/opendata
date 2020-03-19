#!/usr/bin/env bash

wget localhost:8080/data/catalog.rdf -O /var/www/catalog.rdf
wget localhost:8080/data/catalog.xml -O /var/www/catalog.xml
wget localhost:8080/data/catalog.n3 -O /var/www/catalog.n3
wget localhost:8080/data/catalog.ttl -O /var/www/catalog.ttl
wget localhost:8080/data/catalog.jsonld -O /var/www/catalog.jsonld
