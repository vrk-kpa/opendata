from flask import Flask, request, jsonify, make_response
import json
app = Flask(__name__)

TASK_STATUS_ARCHIVER_OK = json.dumps(
    {'success': True,
     'result': {'value': 'Archived successfully',
                'error': json.dumps({
                    'reason': '',
                    'last_success': '2008-10-01',
                    'first_failure': '',
                    'failure_count': 0,
                    }),
                'stack': '',
                'last_updated': '2008-10-10T19:30:37.536836',
                }
     }
    )

request_store = []
task_status = {'archiver': TASK_STATUS_ARCHIVER_OK,
               'qa': None}

# These methods work like CKAN's ones:

@app.route("/api/action/task_status_update_many", methods=['GET', 'POST'])
def task_status_update_many():
    request_store.append({
        "data": request.json,
        "headers": dict(request.headers)
    })
    return 'ok'

@app.route("/api/action/task_status_update", methods=['GET', 'POST'])
def task_status_update():
    request_store.append({
        "data": request.json,
        "headers": dict(request.headers)
    })
    return 'ok'

@app.route("/api/action/task_status_show", methods=['GET', 'POST'])
def task_status_show():
    request_store.append({
        "data": request.json,
        "headers": dict(request.headers)
    })
    try:
        status = task_status[request.json['task_type']]
        if status:
            return status
    except KeyError:
        pass
    resp = make_response('{"success": false}', 404) # JSON
    return resp

@app.route("/api/action/resource_update", methods=['GET', 'POST'])
def resource_update():
    request_store.append({
        "data": request.json,
        "headers": dict(request.headers)
    })
    return 'ok'

# These methods are for test purposes only:

@app.route("/last_request", methods=['GET', 'POST'])
def last_request():
    return jsonify(request_store.pop())

@app.route("/set_task_status/<task_type>/<task_status_str>", methods=['GET'])
def set_task_status(task_type, task_status_str):
    task_status[task_type] = task_status_str
    return 'ok'

@app.route("/set_archiver_task_status_ok", methods=['GET'])
def set_archiver_task_status_ok():
    task_status['archiver'] = TASK_STATUS_ARCHIVER_OK
    return 'ok'

@app.route("/unset_task_status/<task_type>", methods=['GET'])
def unset_task_status(task_type):
    task_status[task_type] = None
    return 'ok'

@app.route("/", methods=['GET', 'POST'])
def ok():
    return 'ok'

if __name__ == "__main__":
    app.run(port=50001)

