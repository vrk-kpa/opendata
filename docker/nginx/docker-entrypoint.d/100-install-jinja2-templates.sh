#!/bin/sh
set -e

minijinja-cli /etc/nginx/jinja2-templates/robots.txt.j2 -o /var/www/static/robots.txt --env
