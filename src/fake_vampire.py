from flask import Flask, jsonify
import math, time

app = Flask(__name__)

@app.route('/taille', methods=['GET'])
def get_size():
    t = time.time()
    val = 800 + 300 * math.sin(t * 0.5)
    return jsonify({"taille": val})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=16040)