import os

# setup sysadmin
sysadmin_username = os.environ.get('SYSADMIN_USER')
sysadmin_roles = os.environ.get('SYSADMIN_ROLES')
# execute drush cmds
if sysadmin_roles is not None:
  for role in sysadmin_roles.split():
    result = os.system(f'drush user:role:add {role} {sysadmin_username}')
    if result != 0:
      print(f'error adding role {role} for user {sysadmin_username}!')
else:
  print(f'no roles to add for user {sysadmin_username}...')

# setup users
for i in range(0, 10):
  # get next key and check if the user's data exists
  key = f'USERS_{str(i)}'
  username = os.environ.get(f'{key}_USER')
  if username is None:
    print(f'{key} does not exist, skipping...')
    continue
  # get user data
  password = os.environ.get(f'{key}_PASS')
  email = os.environ.get(f'{key}_EMAIL')
  roles = os.environ.get(f'{key}_ROLES')
  # execute drush cmds
  result = os.system(f'drush user:create {username} --password="{password}" --mail="{email}"')
  if result != 0:
    print(f'error creating user {username}!')
  if roles is not None:
    for role in roles.split():
      result = os.system(f'drush user:role:add {role} {username}')
      if result != 0:
        print(f'error adding role {role} for user {username}!')
  else:
    print(f'no roles to add for user {username}...')
