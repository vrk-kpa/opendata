import os

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
  # execute drush cmds
  result = os.system(f'drush user:create {username} --password="{password}" --mail="{email}"')
  if result != 0:
    print(f'error creating user {username}!')
