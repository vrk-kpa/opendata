from ckan import model
from ckan.common import c
from ckan.lib import helpers
from sqlalchemy.sql.expression import or_
from pylons import config


def get_user_member(organization_id, state=None):
    """ Helper function to get member states """
    state_query = None
    if not state:
        state_query = or_(model.Member.state == 'active',
                          model.Member.state == 'pending')
    else:
        state_query = or_(model.Member.state == state)

    query = model.Session.query(model.Member).filter(state_query) \
        .filter(model.Member.table_name == 'user').filter(model.Member.group_id == organization_id).filter(model.Member.table_id == c.userobj.id)
    return query.first()


def get_organization_admins(group_id):
    admins = set(model.Session.query(model.User).join(model.Member, model.User.id == model.Member.table_id).
                 filter(model.Member.table_name == "user").filter(model.Member.group_id == group_id).
                 filter(model.Member.state == 'active').filter(model.Member.capacity == 'admin'))

    return admins


def get_ckan_admins():
    admins = set(model.Session.query(model.User).filter(model.User.sysadmin == True))  # noqa

    return admins


def get_default_locale():
    return config.get('ckan.locale_default', 'en')


def get_safe_locale():
    try:
        return helpers.lang()
    except:
        return get_default_locale()
