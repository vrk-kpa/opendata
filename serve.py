import webstore.web as ws
import os

ws.app.config['SQLITE_DIR'] = os.path.join(os.getcwd(), 'archive')
ws.app.config['TESTING'] = True
ws.app.run(port=5001)
