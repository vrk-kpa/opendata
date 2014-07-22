from sqlalchemy.sql.expression import or_
from ckan import model
from ckan.common import c


def get_user_member(organization_id, state=None):
    """ Helper function to get member states """
    state_query = None
    if not state:
        state_query = or_(model.Member.state == 'active', model.Member.state == 'pending')
    else:
        state_query = or_(model.Member.state == state)

    query = model.Session.query(model.Member).filter(state_query) \
        .filter(model.Member.table_name == 'user').filter(model.Member.group_id == organization_id).filter(model.Member.table_id == c.userobj.id)
    return query.first()


def get_organization_admins(group_id):
    return model.Session.query(model.User).join(model.Member, or_(model.User.id == model.Member.table_id, model.User.sysadmin == True)). \
        filter(model.Member.table_name == "user").filter(model.Member.group_id == group_id). \
        filter(model.Member.state == 'active').filter(model.Member.capacity == 'admin')  # noqa
