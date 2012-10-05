from flask import Flask, request, jsonify, Response
import json
app = Flask(__name__)

request_store = []

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
    return jsonify({'success': True,
                     'result': {'value': 'URL request failed',
                                'error': json.dumps({
                                    'reason': 'Server returned 500 error.',
                                    'last_success': '',
                                    'first_failure': '2008-10-01',
                                    'failure_count': 16,
                                    }),
                                'stack': ''}})

@app.route("/api/action/resource_update", methods=['GET', 'POST'])
def resource_update():
    request_store.append({
        "data": request.json,
        "headers": dict(request.headers)
    })
    return 'ok'

@app.route("/last_request", methods=['GET', 'POST'])
def last_request():
    return jsonify(request_store.pop())

@app.route("/", methods=['GET', 'POST'])
def ok():
    return 'ok'

if __name__ == "__main__":
    app.run(port=50001)

