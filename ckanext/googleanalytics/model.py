from ckan import model

def setup():
    connection = model.Session.connection()
    connection.execute("""CREATE TABLE IF NOT EXISTS package_downloads (
                          id integer primary_key,
                          package_id varchar(60),
                          download_visits integer,
                          views_visits integer);""")
    
                          
