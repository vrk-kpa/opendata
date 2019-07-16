from ckan import model
import logging
import sqlalchemy

_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_text = sqlalchemy.text

log = logging.getLogger(__name__)


def _fetch_all_organizations():
    groups = model.Session.query(model.Group) \
        .filter(model.Group.state == u'active') \
        .filter(model.Group.is_organization.is_(True)) \
        .all()  # noqa

    return groups


def get_organizations(context, data_dict=None):
    groups = _fetch_all_organizations()
    groups_list = []
    for group in groups:
        groups_list.append(as_dict(group))
    return groups_list


def get_formats(context, data_dict=None):
    model = context['model']
    session = context['session']

    query = (session.query(
        model.Resource.format,
        _func.count(model.Resource.format).label('total'))
        .filter(_and_(
            model.Resource.state == 'active',
        ))
        .filter(model.Resource.format != '')
        .group_by(model.Resource.format)
        .order_by(_text('total DESC'))
    )

    return [resource.format for resource in query]


def as_dict(obj):
    new_dict = {}
    new_dict['title'] = obj.title
    new_dict['name'] = obj.name
    new_dict['id'] = obj.id
    return new_dict
