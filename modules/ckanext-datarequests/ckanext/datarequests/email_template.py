from ckan.common import _

"""
    A template file for new datarequest notification emails.
"""

subject = _("New datarequest for organization '{organization}'")

message = _("""\
User {user} ({email}) has left a datarequest for organization ({organization}):

--
Title:
{request_title}

Description:
{request_description}
--

{link}

Best regards

Avoindata.fi support
avoindata@vrk.fi
""")
