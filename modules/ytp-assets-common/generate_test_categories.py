# -*- coding: utf-8 -*-
"""
Script for adding categories. These categories are intended for use when working with front-end tasks.

This script is still WIP.

How to run: python generate_test_categories.py <db_username> <db_password>
"""
import sys

import ckan.model as model
from sqlalchemy import create_engine


def _generate_image_urls():
    base_url = u'https://www.betaavoindata.fi/data/uploads/group'
    return [
        u'{}/2019-09-14-125225.580409Ikonit-AvoinData-Regions.svg'.format(base_url),
        u'{}/2019-07-01-102212.846599energia.svg'.format(base_url),
        u'{}/2019-09-14-125054.290257Ikonit-AvoinData-Government.svg'.format(base_url),
        u'{}/2019-07-01-102343.243986Kansainvalistyminen.svg'.format(base_url),
        u'{}/2019-09-14-124019.900929Kulttuuri-liikunta-ulkoilu-ja-matkailu.svg'.format(base_url),
        u'{}/2019-09-14-124758.525007kulttuurijavapaaaika.svg'.format(base_url),
        u'{}/2019-09-14-123833.880147Ikonit--Kuvitukset--Juna.svg'.format(base_url),
        u'{}/2019-07-01-102740.5558642018-07-13-104602.335155Ikonit-AvoinData-Agriculture.svg'.format(base_url),
        u'{}/2019-09-14-124219.193737Liikennejamatkailu.svg'.format(base_url),
        u'{}/2019-07-01-103050.1219632018-03-19-090141.983568hallintojapaatoksenteko.svg'.format(base_url),
        u'{}/2019-09-14-124612.287327Asuminen-ja-muttaminen.svg'.format(base_url),
        u'{}/2018-03-22-162901.594613talous.svg'.format(base_url),
        u'{}/2018-03-22-162934.287485terveysjasosiaalipalvelut.svg'.format(base_url),
        u'{}/2019-09-14-124655.983665Yritystoiminnan-aloittaminen.svg'.format(base_url),
        u'{}/2019-09-14-123926.932875Parisuhde-ja-perhe.svg'.format(base_url),
        u'{}/2018-03-22-163027.730610ymparisto.svg'.format(base_url),
    ]


def _generate_category_data():
    image_urls = _generate_image_urls()
    categories = []

    for i in range(len(image_urls)):
        categories.append(
            {
                'name': u'cat{}'.format(i+1),
                'title': u'Category{}'.format(i+1),
                'image_url': image_urls[i]
            }
        )

    return categories


def _create_group_models():
    data = _generate_category_data()

    return [
        model.Group(
            name=x.get('name'),
            title=x.get('title'),
            image_url=x.get('image_url'),
        ) for x in data
    ]


def create_categories(db_username, db_password):
    engine = create_engine('postgresql://{}:{}@localhost/ckan_default'.format(db_username, db_password))
    session = model.meta.Session
    session.bind = engine

    groups = _create_group_models()

    session.bulk_save_objects(groups)
    session.commit()


if __name__ == '__main__':
    db_username = sys.argv[1]
    db_password = sys.argv[2]

    create_categories(db_username, db_password)
    print('Done...')
