from ckan import model
import logging

log = logging.getLogger(__name__)


def _fetch_all_organizations():
    groups = model.Session.query(model.Group) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .all()  # noqa

    return groups


def get_organizations(context, data_dict):
    groups = _fetch_all_organizations()
    groups_list = []
    for group in groups:
        groups_list.append(as_dict(group))
    return groups_list


def as_dict(obj):
    new_dict = {}
    new_dict['title'] = obj.title
    new_dict['name'] = obj.name
    new_dict['id'] = obj.id
    return new_dict