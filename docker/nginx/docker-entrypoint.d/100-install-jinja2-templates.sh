#!/bin/sh
set -e

jinja2 /etc/nginx/jinja2-templates/robots.txt.j2 -o /var/www/robots.txt
