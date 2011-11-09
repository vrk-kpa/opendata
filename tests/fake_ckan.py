from flask import Flask, request, jsonify
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
    # resource_score in task.py is just checking for a 'openness_score_failure_count'
    # key, but will default to 0 if it doesn't exist
    return jsonify({'success': False})

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

